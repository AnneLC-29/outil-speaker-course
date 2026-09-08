import streamlit as st
import pandas as pd

st.set_page_config(page_title="Outil Speaker Course", layout="wide")

st.title("🎙️ Outil Speaker - Recherche Coureur")

@st.cache_data
def load_data():
    # Chargement du CSV téléchargé depuis Google Sheets
    df = pd.read_csv("coureurs.csv")
    df['DOSSARD'] = pd.to_numeric(df['DOSSARD'], errors='coerce')
    return df

df = load_data()

dossard_input = st.number_input(
    "Saisir le N° de Dossard :", 
    min_value=1, 
    step=1, 
    value=None, 
    placeholder="Tapez le numéro ici..."
)

if dossard_input:
    resultat = df[df['DOSSARD'] == dossard_input]
    
    if not resultat.empty:
        coureur = resultat.iloc[0]
        st.markdown("---")
        
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