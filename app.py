import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Outil Speaker Course", layout="wide")

st.title("🎙️ Outil Speaker - Recherche Coureur")

try:
    # Chargement du fichier CSV
    df = pd.read_csv("coureurs.csv")
    df['DOSSARD'] = pd.to_numeric(df['DOSSARD'], errors='coerce')
    df['Indice BETRAIL'] = pd.to_numeric(df['Indice BETRAIL'], errors='coerce')
    
    # -------------------------------------------------------------
    # 1. ZONE DE RECHERCHE DOSSARD
    # -------------------------------------------------------------
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
            
            # Nom, Prénom & Infos de base
            st.header(f"🏃 {coureur.get('NOM', '')} {coureur.get('PRENOM', '')}")
            st.subheader(f"Épreuve : **{coureur.get('COURSE', 'N/A')}** | Catégorie : **{coureur.get('Catégorie', 'N/A')}** ({coureur.get('SEXE', 'N/A')})")
            
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

    st.markdown("---")
    
    # -------------------------------------------------------------
    # 2. CLASSEMENT POTENTIEL / FAVORIS (TOP 3 PAR COURSE)
    # -------------------------------------------------------------
    st.subheader("🏆 Favoris / Classement potentiel (selon la côte Betrail)")
    
    # Récupérer la liste des parcours uniques
    courses_dispo = df['COURSE'].dropna().unique()
    
    if len(courses_dispo) > 0:
        tabs = st.tabs([f"Epreuve {c}" for c in courses_dispo])
        
        for tab, course_name in zip(tabs, courses_dispo):
            with tab:
                # Filtrer par épreuve et garder uniquement les coureurs avec une cote Betrail valide
                df_course = df[(df['COURSE'] == course_name) & (df['Indice BETRAIL'].notna())].copy()
                
                if not df_course.empty:
                    # Trier par indice Betrail décroissant (du plus fort au moins fort)
                    top3 = df_course.sort_values(by="Indice BETRAIL", ascending=False).head(3)
                    
                    # Sélectionner et nettoyer les colonnes à afficher
                    top3_display = top3[['DOSSARD', 'NOM', 'PRENOM', 'SEXE', 'Indice BETRAIL', 'VILLE']].reset_index(drop=True)
                    top3_display.index += 1  # Rang 1, 2, 3 au lieu de 0, 1, 2
                    
                    st.dataframe(
                        top3_display, 
                        use_container_width=True,
                        column_config={
                            "DOSSARD": "Dossard",
                            "NOM": "Nom",
                            "PRENOM": "Prénom",
                            "SEXE": "Sexe",
                            "Indice BETRAIL": st.column_config.NumberColumn("Cote Betrail", format="%.2f"),
                            "VILLE": "Ville / Club"
                        }
                    )
                else:
                    st.write("Aucun indice Betrail renseigné pour cette épreuve.")

except Exception as e:
    st.error(f"Erreur lors de la lecture des données : {e}")
