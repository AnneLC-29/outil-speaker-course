import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Configuration de la page
st.set_page_config(page_title="Outil Speaker Course", layout="wide")

st.title("🎙️ Outil Speaker - Foulées Raids Dingues")

@st.cache_data
def load_and_process_data():
    # Chargement du fichier CSV
    df = pd.read_csv("coureurs.csv")
    df['DOSSARD'] = pd.to_numeric(df['DOSSARD'], errors='coerce')
    df['Indice BETRAIL'] = pd.to_numeric(df['Indice BETRAIL'], errors='coerce')
    
    if 'SEXE' in df.columns:
        df['SEXE'] = df['SEXE'].astype(str).str.strip().str.upper()

    # Découpage de la colonne VILLE pour séparer la Ville et le Club
    # Exemple : "CHAUCHE (85140) / RAID'APTE" -> Ville: CHAUCHE (85140), Club: RAID'APTE
    def extract_club(val):
        if pd.isna(val):
            return None
        parts = str(val).split('/')
        if len(parts) > 1:
            return parts[1].strip()
        return None

    def extract_clean_city(val):
        if pd.isna(val):
            return ""
        # Prendre ce qui est avant le "/" s'il y en a un
        city_part = str(val).split('/')[0].strip()
        # Nettoyer les code postaux entre parenthèses pour la géolocalisation
        clean_city = city_part.split('(')[0].strip()
        return clean_city

    df['CLUB'] = df['VILLE'].apply(extract_club)
    df['VILLE_CLEAN'] = df['VILLE'].apply(extract_clean_city)
    
    return df

try:
    df = load_and_process_data()

    # Création des onglets principaux
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
                
                # Nom, Prénom & Infos
                st.header(f"🏃 {coureur.get('NOM', '')} {coureur.get('PRENOM', '')}")
                
                club_str = f" | Club : **{coureur['CLUB']}**" if pd.notna(coureur['CLUB']) and coureur['CLUB'] != "" else ""
                st.subheader(f"Épreuve : **{coureur.get('COURSE', 'N/A')}** | Catégorie : **{coureur.get('Catégorie', 'N/A')}** ({coureur.get('SEXE', 'N/A')}){club_str}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="Ville / Club", value=str(coureur.get('VILLE', 'Inconnu')))
                
                with col2:
                    betrail = coureur.get('Indice BETRAIL', 'N/A')
                    st.metric(label="Indice Betrail", value=f"{betrail}" if pd.notna(betrail) else "Non renseigné")
                    
                with col3:
                    classement = coureur.get('CLASSEMENT', 'N/A')
                    st.metric(label="Rang théorique", value=f"N° {classement}" if pd.notna(classement) else "N/A")

                st.markdown("---")
                
                # Commentaires et Historique
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
                    
                    # --- TOP 3 FEMMES ---
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

                    # --- TOP 3 HOMMES ---
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
    # ONGLET 3 : CARTE ET CLUBS REPRESENTES
    # -------------------------------------------------------------
    with tab_stats:
        col_map, col_clubs = st.columns([3, 2])
        
        # --- CLASSEMENT DES CLUBS ---
        with col_clubs:
            st.subheader("🛡️ Clubs & Associations les plus représentés")
            df_clubs = df[df['CLUB'].notna() & (df['CLUB'] != "")]
            
            if not df_clubs.empty:
                stats_clubs = df_clubs['CLUB'].value_counts().reset_index()
                stats_clubs.columns = ['Club / Association', 'Nombre d\'inscrits']
                
                st.dataframe(
                    stats_clubs, 
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.write("Aucun club renseigné dans les données.")

        # --- CARTE INTERACTIVE DES VILLES ---
        with col_map:
            st.subheader("🗺️ Répartition géographique des coureurs")
            
            @st.cache_data
            def geolocate_villes(villes_list):
                geolocator = Nominatim(user_agent="speaker_race_app")
                geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.2)
                
                coords = []
                for ville in villes_list:
                    if ville and len(ville) > 1:
                        try:
                            location = geocode(f"{ville}, France")
                            if location:
                                coords.append({
                                    'ville': ville,
                                    'latitude': location.latitude,
                                    'longitude': location.longitude
                                })
                        except Exception:
                            pass
                return pd.DataFrame(coords)

            villes_uniques = [v for v in df['VILLE_CLEAN'].dropna().unique() if v != ""]
            
            with st.spinner("Chargement de la carte des villes..."):
                df_coords = geolocate_villes(villes_uniques)
                
                if not df_coords.empty:
                    # Associer le nombre de coureurs par ville
                    counts = df['VILLE_CLEAN'].value_counts().reset_index()
                    counts.columns = ['ville', 'Nb Coureurs']
                    
                    df_map_data = pd.merge(df_coords, counts, on='ville', how='inner')
                    
                    # Affichage de la carte native Streamlit
                    st.map(
                        df_map_data, 
                        latitude='latitude', 
                        longitude='longitude', 
                        size='Nb Coureurs',
                        color='#FF4B4B'
                    )
                else:
                    st.write("Impossible de géolocaliser les villes pour le moment.")

except Exception as e:
    st.error(f"Erreur lors de l'exécution : {e}")
