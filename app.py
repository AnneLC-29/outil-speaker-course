import streamlit as st
import pandas as pd
import re

# Configuration de la page
st.set_page_config(page_title="Outil Speaker Course", layout="wide")

st.title("🎙️ Outil Speaker - Foulées Raids Dingues")

# Dictionnaire des coordonnées des départements
DEPT_COORDS = {
    '85': {'lat': 46.6705, 'lon': -1.4264, 'nom': 'Vendée'},
    '17': {'lat': 45.8333, 'lon': -0.6667, 'nom': 'Charente-Maritime'},
    '79': {'lat': 46.5333, 'lon': -0.3333, 'nom': 'Deux-Sèvres'},
    '44': {'lat': 47.3167, 'lon': -1.5500, 'nom': 'Loire-Atlantique'},
    '49': {'lat': 47.4167, 'lon': -0.5500, 'nom': 'Maine-et-Loire'},
    '86': {'lat': 46.5833, 'lon': 0.3333, 'nom': 'Vienne'},
    '75': {'lat': 48.8566, 'lon': 2.3522, 'nom': 'Paris'},
    '13': {'lat': 43.5297, 'lon': 5.4474, 'nom': 'Bouches-du-Rhône'},
    '91': {'lat': 48.5333, 'lon': 2.2500, 'nom': 'Essonne'}
}

@st.cache_data
def load_and_process_data():
    df = pd.read_csv("coureurs.csv")
    df['DOSSARD'] = pd.to_numeric(df['DOSSARD'], errors='coerce')
    df['Indice BETRAIL'] = pd.to_numeric(df['Indice BETRAIL'], errors='coerce')
    
    if 'SEXE' in df.columns:
        df['SEXE'] = df['SEXE'].astype(str).str.strip().str.upper()

    def extract_club(val):
        if pd.isna(val):
            return None
        parts = str(val).split('/')
        if len(parts) > 1:
            return parts[1].strip()
        return None

    def extract_dept(val):
        if pd.isna(val):
            return None
        match = re.search(r'\((\d{2})\d{3}\)', str(val))
        if match:
            return match.group(1)
        return None

    df['CLUB'] = df['VILLE'].apply(extract_club)
    df['DEPT'] = df['VILLE'].apply(extract_dept)
    
    return df

try:
    df = load_and_process_data()

    tab_search, tab_favoris, tab_stats = st.tabs([
        "🔎 Recherche Dossard", 
        "🏆 Favoris & Cotes Betrail", 
        "📊 Origine & Clubs"
    ])

    # -------------------------------------------------------------
    # ONGLET 1 : RECHERCHE DOSSARD
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
                
                club_str = f" | Club : **{coureur['CLUB']}**" if pd.notna(coureur['CLUB']) and coureur['CLUB'] != "" else ""
                st.subheader(f"Épreuve : **{coureur.get('COURSE', 'N/A')}** | Catégorie : **{coureur.get('Catégorie', 'N/A')}** ({coureur.get('SEXE', 'N/A')}){club_str}")
                
                # --- CALCUL DYNAMIQUE DU RANG PAR COTE BETRAIL ---
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
                    st.metric(label="Ville / Club", value=str(coureur.get('VILLE', 'Inconnu')))
                
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
            else:
                st.warning(f"Aucun coureur trouvé avec le dossard N° {dossard_input}")

    # -------------------------------------------------------------
    # ONGLET 2 : FAVORIS ET COTES BETRAIL
    # -------------------------------------------------------------
    with tab_favoris:
        st.subheader("🏆 Favoris / Classement potentiel par cote Betrail")
        courses_dispo = df['COURSE'].dropna().unique()
        
        if len(courses_dispo) > 0:
            sub_tabs = st.tabs([f"Épreuve {c}" for c in courses_dispo])
            
            for tab, course_name in zip(sub_tabs, courses_dispo):
                with tab:
                    df_course = df[(df['COURSE'] == course_name) & (df['Indice BETRAIL'].notna())].copy()
                    col_femmes, col_hommes = st.columns(2)
                    
                    with col_femmes:
                        st.markdown("#### 👩 Top 3 Femmes")
                        top3_f = df_course[df_course['SEXE'] == 'F'].sort_values(by="Indice BETRAIL", ascending=False).head(3)
                        
                        if not top3_f.empty:
                            top3_f_display = top3_f[['DOSSARD', 'NOM', 'PRENOM', 'Indice BETRAIL', 'VILLE']].reset_index(drop=True)
                            top3_f_display.index += 1
                            st.dataframe(
                                top3_f_display, 
                                use_container_width=True,
                                column_config={
                                    "DOSSARD": "Dossard",
                                    "NOM": "Nom",
                                    "PRENOM": "Prénom",
                                    "Indice BETRAIL": st.column_config.NumberColumn("Cote Betrail", format="%.2f"),
                                    "VILLE": "Ville / Club"
                                }
                            )
                        else:
                            st.write("Aucune donnée disponible.")

                    with col_hommes:
                        st.markdown("#### 👨 Top 3 Hommes")
                        top3_h = df_course[df_course['SEXE'] == 'H'].sort_values(by="Indice BETRAIL", ascending=False).head(3)
                        
                        if not top3_h.empty:
                            top3_h_display = top3_h[['DOSSARD', 'NOM', 'PRENOM', 'Indice BETRAIL', 'VILLE']].reset_index(drop=True)
                            top3_h_display.index += 1
                            st.dataframe(
                                top3_h_display, 
                                use_container_width=True,
                                column_config={
                                    "DOSSARD": "Dossard",
                                    "NOM": "Nom",
                                    "PRENOM": "Prénom",
                                    "Indice BETRAIL": st.column_config.NumberColumn("Cote Betrail", format="%.2f"),
                                    "VILLE": "Ville / Club"
                                }
                            )
                        else:
                            st.write("Aucune donnée disponible.")

    # -------------------------------------------------------------
    # ONGLET 3 : ORIGINES ET CLUBS
    # -------------------------------------------------------------
    with tab_stats:
        col_map, col_clubs = st.columns([3, 2])
        
        with col_clubs:
            st.subheader("🛡️ Clubs & Associations les plus représentés")
            df_clubs = df[df['CLUB'].notna() & (df['CLUB'] != "")]
            
            if not df_clubs.empty:
                stats_clubs = df_clubs['CLUB'].value_counts().reset_index()
                stats_clubs.columns = ['Club / Association', 'Nombre d\'inscrits']
                st.dataframe(stats_clubs, use_container_width=True, hide_index=True)
            else:
                st.write("Aucun club renseigné dans les données.")

        with col_map:
            st.subheader("🗺️ Répartition par Département")
            
            dept_counts = df['DEPT'].value_counts().reset_index()
            dept_counts.columns = ['DEPT', 'Nb Coureurs']
            
            map_data = []
            for _, row in dept_counts.iterrows():
                dept = row['DEPT']
                if dept in DEPT_COORDS:
                    map_data.append({
                        'latitude': DEPT_COORDS[dept]['lat'],
                        'longitude': DEPT_COORDS[dept]['lon'],
                        'Département': f"{dept} - {DEPT_COORDS[dept]['nom']}",
                        'Nb Coureurs': row['Nb Coureurs']
                    })
            
            df_map = pd.DataFrame(map_data)
            
            if not df_map.empty:
                st.map(
                    df_map, 
                    latitude='latitude', 
                    longitude='longitude', 
                    size='Nb Coureurs',
                    color='#FF4B4B'
                )
                
                st.dataframe(
                    df_map[['Département', 'Nb Coureurs']], 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.write("Aucune donnée de département valide trouvée.")

except Exception as e:
    st.error(f"Erreur lors de l'exécution : {e}")