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
                
                # EN-TÊTE
                st.header(f"🏃 {coureur.get('NOM', '')} {coureur.get('PRENOM', '')}")
                
                club_name = coureur['CLUB']
                is_club_valid = club_name != "Indépendant / Non renseigné"
                
                st.subheader(f"Épreuve : **{coureur.get('COURSE', 'N/A')}** | Catégorie : **{coureur.get('Catégorie', 'N/A')}** ({coureur.get('SEXE', 'N/A')})")
                
                if is_club_valid:
                    st.success(f"🛡️ **Club / Association : {club_name}**")

                # CALCUL DYNAMIQUE DU RANG
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
                
                # SECTION COMMENTAIRES & HISTORIQUE
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

                # SECTION LOCALISATION ET DETAIL PAR COMMUNE / CLUB
                st.markdown("---")
                st.markdown("### 📍 Origine & Représentation Locale")
                
                nom_ville = coureur['NOM_VILLE']
                cp_ville = coureur['CODE_POSTAL']
                
                # Coureurs de la même ville
                df_ville_all = df[(df['NOM_VILLE'] == nom_ville) & (df['CODE_POSTAL'] == cp_ville)]
                nb_coureurs_ville = len(df_ville_all)
                
                # Alignement côte à côte (Carte à gauche, Détails à droite)
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
                            popup=f"<b>{coureur['VILLE_CLEAN']}</b><br>{nb_coureurs_ville} inscrit(s)",
                            tooltip=coureur['VILLE_CLEAN'],
                            icon=folium.Icon(color="red", icon="user")
                        ).add_to(m_coureur)
                        
                        st_folium(m_coureur, width="100%", height=280, key=f"map_coureur_{dossard_input}")
                    else:
                        st.write("Carte non disponible.")

                with col_info_c:
                    st.markdown(f"#### 🏘️ Inscrits de {coureur['NOM_VILLE']} ({nb_coureurs_ville} coureurs)")
                    
                    # Répartition par distance
                    dist_counts = df_ville_all['COURSE'].value_counts()
                    dist_str = " | ".join([f"**{course}** : {cnt}" for course, cnt in dist_counts.items()])
                    st.markdown(f"📊 **Répartition :** {dist_str}")
                    
                    # Tableau récapitulatif nominatif
                    df_v_display = df_ville_all[['DOSSARD', 'NOM', 'PRENOM', 'COURSE', 'Catégorie']].sort_values(by='COURSE').reset_index(drop=True)
                    st.dataframe(df_v_display, use_container_width=True, hide_index=True)

                # AUTRES MEMBRES DU CLUB SI APPLICABLE
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