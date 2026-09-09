import streamlit as st
import pandas as pd
import re
import requests
import folium
from streamlit_folium import st_folium

# Configuration de la page
st.set_page_config(page_title="Outil Speaker Course", layout="wide")

st.title("🎙️ Outil Speaker - Foulées Raids Dingues")

# Dictionnaire des catégories FFA avec tranches d'âge
CATEGORIES_AGE = {
    'BB': 'Baby (3-5 ans)',
    'EA': 'Éveil Athlé (6-9 ans)',
    'PO': 'Poussins (10-11 ans)',
    'BE': 'Benjamins (12-13 ans)',
    'MI': 'Minimes (14-15 ans)',
    'CA': 'Cadets (16-17 ans)',
    'JU': 'Juniors (18-19 ans)',
    'ES': 'Espoirs (20-22 ans)',
    'SE': 'Séniors (23-34 ans)',
    'M0': 'Master 0 (35-39 ans)',
    'M1': 'Master 1 (40-44 ans)',
    'M2': 'Master 2 (45-49 ans)',
    'M3': 'Master 3 (50-54 ans)',
    'M4': 'Master 4 (55-59 ans)',
    'M5': 'Master 5 (60-64 ans)',
    'M6': 'Master 6 (65-69 ans)',
    'M7': 'Master 7 (70-74 ans)',
    'M8': 'Master 8 (75-79 ans)',
    'M9': 'Master 9 (80-84 ans)',
    'M10': 'Master 10 (85+ ans)'
}

ORDRE_CATEGORIES = list(CATEGORIES_AGE.keys())

@st.cache_data
def load_and_process_data():
    df = pd.read_csv("coureurs.csv")
    
    # Nettoyage : ne garder que les lignes avec un nom valide
    if 'NOM' in df.columns:
        df = df[df['NOM'].notna() & (df['NOM'].astype(str).str.strip() != "")]
        
    df['DOSSARD'] = pd.to_numeric(df['DOSSARD'], errors='coerce')
    df['Indice BETRAIL'] = pd.to_numeric(df['Indice BETRAIL'], errors='coerce')
    
    if 'SEXE' in df.columns:
        df['SEXE'] = df['SEXE'].astype(str).str.strip().str.upper()

    def extract_club(val):
        if pd.isna(val):
            return "Indépendant / Non renseigné"
        parts = str(val).split('/')
        if len(parts) > 1 and parts[1].strip() != "":
            return parts[1].strip()
        return "Indépendant / Non renseigné"

    def extract_ville_cp(val):
        if pd.isna(val):
            return "Inconnue", None
        ville_part = str(val).split('/')[0].strip()
        match = re.search(r'^(.*?)\s*\((\d{5})\)', ville_part)
        if match:
            nom_ville = match.group(1).strip()
            cp = match.group(2).strip()
            return nom_ville, cp
        return ville_part, None

    df['CLUB'] = df['VILLE'].apply(extract_club)
    res_villes = df['VILLE'].apply(extract_ville_cp)
    df['NOM_VILLE'] = [r[0] for r in res_villes]
    df['CODE_POSTAL'] = [r[1] for r in res_villes]
    df['VILLE_CLEAN'] = df.apply(lambda r: f"{r['NOM_VILLE']} ({r['CODE_POSTAL']})" if pd.notna(r['CODE_POSTAL']) else r['NOM_VILLE'], axis=1)
    
    return df

@st.cache_data
def geolocaliser_communes(df_villes):
    coords = []
    for _, row in df_villes.iterrows():
        cp = row['CODE_POSTAL']
        ville = row['NOM_VILLE']
        
        if pd.notna(cp):
            try:
                url = f"https://geo.api.gouv.fr/communes?codePostal={cp}&fields=centre,nom&format=json"
                response = requests.get(url, timeout=3).json()
                
                if response:
                    commune_match = response[0]
                    for item in response:
                        if item['nom'].lower() == str(ville).lower():
                            commune_match = item
                            break
                    
                    lon, lat = commune_match['centre']['coordinates']
                    coords.append({
                        'NOM_VILLE': ville,
                        'CODE_POSTAL': cp,
                        'Ville_CP': f"{ville} ({cp})",
                        'latitude': lat,
                        'longitude': lon
                    })
            except Exception:
                pass
    return pd.DataFrame(coords)

try:
    df = load_and_process_data()

    tab_general, tab_search, tab_favoris, tab_stats = st.tabs([
        "📈 Infos Générales & Stats",
        "🔎 Recherche Dossard", 
        "🏆 Favoris & Cotes Betrail", 
        "📊 Origine & Clubs"
    ])

    # -------------------------------------------------------------
    # ONGLET 1 : INFOS GÉNÉRALES & STATISTIQUES (AVEC MARCHE)
    # -------------------------------------------------------------
    with tab_general:
        st.subheader("📈 Statistiques Générales de l'Édition")
        
        total_inscrits = len(df)
        nb_hommes = len(df[df['SEXE'] == 'H'])
        nb_femmes = len(df[df['SEXE'] == 'F'])
        pct_femmes = (nb_femmes / total_inscrits * 100) if total_inscrits > 0 else 0
        pct_hommes = (nb_hommes / total_inscrits * 100) if total_inscrits > 0 else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Participants", f"{total_inscrits} inscrits")
        m2.metric("Hommes", f"{nb_hommes} ({pct_hommes:.1f}%)")
        m3.metric("Femmes", f"{nb_femmes} ({pct_femmes:.1f}%)")
        
        if 'COURSE' in df.columns and not df['COURSE'].dropna().empty:
            top_course = df['COURSE'].value_counts().idxmax()
            m4.metric("Épreuve reine", f"{top_course}")

        st.markdown("---")
        
        c_left, c_right = st.columns(2)
        
        # REPARTITION PAR EPREUVE (INCLUT LA MARCHE)
        with c_left:
            st.markdown("### 🏃‍♂️ Inscrits par Épreuve & Marche")
            
            if 'COURSE' in df.columns:
                df_courses = df.groupby(['COURSE', 'SEXE']).size().unstack(fill_value=0)
                if 'H' not in df_courses.columns: df_courses['H'] = 0
                if 'F' not in df_courses.columns: df_courses['F'] = 0
                
                df_courses['Total'] = df_courses['H'] + df_courses['F']
                
                st.bar_chart(df_courses[['Total']], color="#FF4B4B")
                
                st.dataframe(
                    df_courses.reset_index(),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "COURSE": "Épreuve / Distance",
                        "H": "Hommes",
                        "F": "Femmes",
                        "Total": "Total Inscrits"
                    }
                )

        # REPARTITION PAR CATEGORIE ET TRANCHE D'AGE
        with c_right:
            st.markdown("### 🏷️ Répartition par Catégorie (triée par âge)")
            
            if 'Catégorie' in df.columns:
                df_cat = df['Catégorie'].value_counts().reset_index()
                df_cat.columns = ['Code_Cat', 'Nombre']
                df_cat['Code_clean'] = df_cat['Code_Cat'].astype(str).str.strip().str.upper()
                
                df_cat = df_cat[df_cat['Code_clean'].isin(ORDRE_CATEGORIES)].copy()
                df_cat['Code_clean'] = pd.Categorical(
                    df_cat['Code_clean'], 
                    categories=ORDRE_CATEGORIES, 
                    ordered=True
                )
                
                df_cat = df_cat.sort_values(by='Code_clean').reset_index(drop=True)
                df_cat['Catégorie & Plage d\'âge'] = df_cat['Code_clean'].apply(
                    lambda x: f"{x} - {CATEGORIES_AGE.get(str(x), 'Non spécifié')}"
                )
                
                chart_data = df_cat.set_index('Code_clean')[['Nombre']]
                st.bar_chart(chart_data)
                
                st.dataframe(
                    df_cat[['Catégorie & Plage d\'âge', 'Nombre']], 
                    use_container_width=True, 
                    hide_index=True
                )

    # -------------------------------------------------------------
    # ONGLET 2 : RECHERCHE DOSSARD (COUREURS SEULEMENT)
    # -------------------------------------------------------------
    with tab_search:
        dossard_input = st.number_input(
            "Saisir le N° de Dossard :", 
            min_value=1, 
            step=1, 
            value=None, 
            placeholder="Tapez le numéro de dossard ici..."
        )

        if dossard_input:
            resultat = df[df['DOSSARD'] == dossard_input]
            
            if not resultat.empty:
                coureur = resultat.iloc[0]
                st.markdown("---")
                
                st.header(f"🏃 {coureur.get('NOM', '')} {coureur.get('PRENOM', '')}")
                
                club_name = coureur['CLUB']
                is_club_valid = club_name != "Indépendant / Non renseigné"
                
                cat_code = str(coureur.get('Catégorie', 'N/A')).strip().upper()
                cat_label = CATEGORIES_AGE.get(cat_code, cat_code)
                
                st.subheader(f"Épreuve : **{coureur.get('COURSE', 'N/A')}** | Catégorie : **{cat_label}** ({coureur.get('SEXE', 'N/A')})")
                
                if is_club_valid:
                    st.success(f"🛡️ **Club / Association : {club_name}**")

                rang_str = "N/A"
                if pd.notna(coureur.get('Indice BETRAIL')):
                    df_meme_course_sexe = df[
                        (df['COURSE'] == coureur['COURSE']) & 
                        (df['SEXE'] == coureur['SEXE']) & 
                        (df['Indice BETRAIL'].notna())
                    ].sort_values(by='Indice BETRAIL', ascending=False).reset_index(drop=True)
                    
                    pos = df_meme_course_sexe[df_meme_course_sexe['DOSSARD'] == dossard_input].index
                    if not pos.empty:
                        rang_str = f"N° {pos[0] + 1} ({coureur['SEXE']})"

                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="Ville / Origine", value=str(coureur.get('VILLE_CLEAN', 'Inconnu')))
                
                with col2:
                    betrail = coureur.get('Indice BETRAIL', 'N/A')
                    st.metric(label="Indice Betrail", value=f"{betrail}" if pd.notna(betrail) else "Non renseigné")
                    
                with col3:
                    st.metric(label="Rang théorique", value=rang_str)

                st.markdown("---")
                
                col_com, col_hist = st.columns(2)
                
                with col_com:
                    st.markdown("### 📝 Commentaires / Notes Speaker")
                    commentaires = coureur.get('COMMENTAIRES', None)
                    if pd.notna(commentaires) and str(commentaires).strip() != "":
                        st.info(f"**Note :** {commentaires}")
                    else:
                        st.write("Aucun commentaire spécifique.")

                with col_hist:
                    st.markdown("### 📜 Historique édition précédente")
                    f2025 = coureur.get('FOULEES 2025', None)
                    f2024 = coureur.get('FOULEES 2024', None)
                    
                    if pd.notna(f2025):
                        st.write(f"- **Édition 2025 :** {f2025}")
                    if pd.notna(f2024):
                        st.write(f"- **Édition 2024 :** {f2024}")
                    if pd.isna(f2025) and pd.isna(f2024):
                        st.write("Pas de participation enregistrée en 2024/2025.")

                st.markdown("---")
                st.markdown("### 📍 Origine & Représentation Locale")
                
                nom_ville = coureur['NOM_VILLE']
                cp_ville = coureur['CODE_POSTAL']
                
                df_ville_all = df[(df['NOM_VILLE'] == nom_ville) & (df['CODE_POSTAL'] == cp_ville)]
                nb_coureurs_ville = len(df_ville_all)
                
                col_map_c, col_info_c = st.columns([1, 1])
                
                with col_map_c:
                    st.markdown(f"#### 🗺️ Localisation : {coureur['VILLE_CLEAN']}")
                    df_v_unique = pd.DataFrame([{'NOM_VILLE': nom_ville, 'CODE_POSTAL': cp_ville}])
                    coords_c = geolocaliser_communes(df_v_unique)
                    
                    if not coords_c.empty:
                        lat = coords_c.iloc[0]['latitude']
                        lon = coords_c.iloc[0]['longitude']
                        
                        m_coureur = folium.Map(
                            location=[lat, lon], 
                            zoom_start=11,
                            tiles="https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
                            attr="&copy; OpenStreetMap France"
                        )
                        folium.Marker(
                            location=[lat, lon],
                            popup=f"<b>{coureur['VILLE_CLEAN']}</b><br>{nb_coureurs_ville} participant(s)",
                            tooltip=coureur['VILLE_CLEAN'],
                            icon=folium.Icon(color="red", icon="user")
                        ).add_to(m_coureur)
                        
                        st_folium(m_coureur, width="100%", height=280, key=f"map_coureur_{dossard_input}")
                    else:
                        st.write("Carte non disponible.")

                with col_info_c:
                    st.markdown(f"#### 🏘️ Inscrits de {coureur['NOM_VILLE']} ({nb_coureurs_ville} participants)")
                    
                    dist_counts = df_ville_all['COURSE'].value_counts()
                    dist_str = " | ".join([f"**{course}** : {cnt}" for course, cnt in dist_counts.items()])
                    st.markdown(f"📊 **Répartition :** {dist_str}")
                    
                    df_v_display = df_ville_all[['DOSSARD', 'NOM', 'PRENOM', 'COURSE', 'Catégorie']].sort_values(by='COURSE').reset_index(drop=True)
                    st.dataframe(df_v_display, use_container_width=True, hide_index=True)

                if is_club_valid:
                    st.markdown("---")
                    df_club_all = df[df['CLUB'] == club_name]
                    st.markdown(f"### 🛡️ Membres de l'association **{club_name}** ({len(df_club_all)} inscrits)")
                    
                    dist_club_counts = df_club_all['COURSE'].value_counts()
                    dist_club_str = " | ".join([f"**{course}** : {cnt}" for course, cnt in dist_club_counts.items()])
                    st.markdown(f"📊 **Répartition par épreuve :** {dist_club_str}")
                    
                    df_club_display = df_club_all[['DOSSARD', 'NOM', 'PRENOM', 'COURSE', 'Catégorie', 'SEXE']].sort_values(by='COURSE').reset_index(drop=True)
                    st.dataframe(df_club_display, use_container_width=True, hide_index=True)

            else:
                st.warning(f"Aucun coureur trouvé avec le dossard N° {dossard_input}")

    # -------------------------------------------------------------
    # ONGLET 3 : FAVORIS ET COTES BETRAIL (EPREUVES DE TRAIL SEULEMENT)
    # -------------------------------------------------------------
    with tab_favoris:
        st.subheader("🏆 Favoris / Classement potentiel par cote Betrail")
        
        # Filtrer uniquement les épreuves qui contiennent au moins une cote Betrail (exclut la marche)
        df_trails = df[df['Indice BETRAIL'].notna()]
        courses_trail_raw = df_trails['COURSE'].dropna().unique()
        
        def get_distance_num(course_str):
            match = re.search(r'(\d+)', str(course_str))
            return int(match.group(1)) if match else 999
            
        courses_dispo = sorted(courses_trail_raw, key=get_distance_num)
        
        if len(courses_dispo) > 0:
            for course_name in courses_dispo:
                st.markdown("---")
                st.markdown(f"### 🚩 Épreuve : **{course_name}**")
                
                df_course = df_trails[df_trails['COURSE'] == course_name].copy()
                col_femmes, col_hommes = st.columns(2)
                
                # TOP 5 FEMMES
                with col_femmes:
                    st.markdown("#### 👩 Top 5 Femmes")
                    top5_f = df_course[df_course['SEXE'] == 'F'].sort_values(by="Indice BETRAIL", ascending=False).head(5)
                    
                    if not top5_f.empty:
                        top5_f_display = top5_f[['DOSSARD', 'NOM', 'PRENOM', 'Indice BETRAIL', 'VILLE_CLEAN']].reset_index(drop=True)
                        top5_f_display.index += 1
                        st.dataframe(
                            top5_f_display, 
                            use_container_width=True,
                            column_config={
                                "DOSSARD": "Dossard",
                                "NOM": "Nom",
                                "PRENOM": "Prénom",
                                "Indice BETRAIL": st.column_config.NumberColumn("Cote Betrail", format="%.2f"),
                                "VILLE_CLEAN": "Ville / Origine"
                            }
                        )
                    else:
                        st.write("Aucune donnée disponible.")

                # TOP 5 HOMMES
                with col_hommes:
                    st.markdown("#### 👨 Top 5 Hommes")
                    top5_h = df_course[df_course['SEXE'] == 'H'].sort_values(by="Indice BETRAIL", ascending=False).head(5)
                    
                    if not top5_h.empty:
                        top5_h_display = top5_h[['DOSSARD', 'NOM', 'PRENOM', 'Indice BETRAIL', 'VILLE_CLEAN']].reset_index(drop=True)
                        top5_h_display.index += 1
                        st.dataframe(
                            top5_h_display, 
                            use_container_width=True,
                            column_config={
                                "DOSSARD": "Dossard",
                                "NOM": "Nom",
                                "PRENOM": "Prénom",
                                "Indice BETRAIL": st.column_config.NumberColumn("Cote Betrail", format="%.2f"),
                                "VILLE_CLEAN": "Ville / Origine"
                            }
                        )
                    else:
                        st.write("Aucune donnée disponible.")

    # -------------------------------------------------------------
    # ONGLET 4 : ORIGINES ET CLUBS (INCLUT COUREURS ET MARCHEURS)
    # -------------------------------------------------------------
    with tab_stats:
        col_map, col_clubs = st.columns([3, 2])
        
        with col_clubs:
            st.subheader("🛡️ Détail par Club / Association")
            
            clubs_valides = [c for c in df['CLUB'].unique() if c != "Indépendant / Non renseigné"]
            stats_clubs = df[df['CLUB'].isin(clubs_valides)]['CLUB'].value_counts().reset_index()
            stats_clubs.columns = ['Club', 'Nb Inscrits']
            
            selected_club = st.selectbox(
                "Sélectionnez un club pour voir la liste des participants :",
                options=["-- Choisir un club --"] + list(stats_clubs['Club'])
            )
            
            if selected_club and selected_club != "-- Choisir un club --":
                coureurs_club = df[df['CLUB'] == selected_club][['DOSSARD', 'NOM', 'PRENOM', 'COURSE', 'Catégorie', 'SEXE']].sort_values(by='COURSE').reset_index(drop=True)
                st.write(f"👥 **{len(coureurs_club)} participant(s)** inscrit(s) pour **{selected_club}** :")
                st.dataframe(coureurs_club, use_container_width=True, hide_index=True)
            else:
                st.markdown("**Top des clubs les plus représentés :**")
                st.dataframe(stats_clubs.head(10), use_container_width=True, hide_index=True)

        with col_map:
            st.subheader("🗺️ Carte & Détail par Ville")
            
            df_villes_uniques = df[['NOM_VILLE', 'CODE_POSTAL']].dropna().drop_duplicates()
            df_coords = geolocaliser_communes(df_villes_uniques)
            
            if not df_coords.empty:
                counts_ville = df.groupby(['NOM_VILLE', 'CODE_POSTAL']).size().reset_index(name='Nb Coureurs')
                df_map_final = pd.merge(df_coords, counts_ville, on=['NOM_VILLE', 'CODE_POSTAL'])
                
                center_lat = df_map_final['latitude'].mean()
                center_lon = df_map_final['longitude'].mean()
                
                m = folium.Map(
                    location=[center_lat, center_lon], 
                    zoom_start=9,
                    tiles="https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
                    attr="&copy; OpenStreetMap France"
                )
                
                for _, row in df_map_final.iterrows():
                    c_list = df[(df['NOM_VILLE'] == row['NOM_VILLE']) & (df['CODE_POSTAL'] == row['CODE_POSTAL'])]
                    coureurs_html = "<br>".join([f"- {r['NOM']} {r['PRENOM']} ({r['COURSE']})" for _, r in c_list.iterrows()])
                    
                    popup_content = f"""
                    <div style='font-size:13px; min-width:180px;'>
                        <b>📍 {row['Ville_CP']}</b><br>
                        <i>{row['Nb Coureurs']} participant(s) :</i><br>{coureurs_html}
                    </div>
                    """
                    
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=5 + (row['Nb Coureurs'] * 2),
                        popup=folium.Popup(popup_content, max_width=300),
                        color="#FF4B4B",
                        fill=True,
                        fill_color="#FF4B4B",
                        fill_opacity=0.6
                    ).add_to(m)
                
                st_folium(m, width="100%", height=400, key="map_globale")
                
                selected_ville = st.selectbox(
                    "Ou sélectionnez une ville dans la liste :",
                    options=["-- Choisir une ville --"] + list(df_map_final['Ville_CP'].sort_values())
                )
                
                if selected_ville and selected_ville != "-- Choisir une ville --":
                    coureurs_ville = df[df['VILLE_CLEAN'] == selected_ville][['DOSSARD', 'NOM', 'PRENOM', 'COURSE', 'Catégorie']].sort_values(by='COURSE').reset_index(drop=True)
                    st.write(f"🏘️ **{len(coureurs_ville)} participant(s)** originaire(s) de **{selected_ville}** :")
                    st.dataframe(coureurs_ville, use_container_width=True, hide_index=True)
                else:
                    st.markdown("**Top 10 des villes les plus représentées :**")
                    top10_villes = df_map_final[['Ville_CP', 'Nb Coureurs']].sort_values(by='Nb Coureurs', ascending=False).head(10)
                    st.dataframe(top10_villes, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erreur lors de l'exécution : {e}")