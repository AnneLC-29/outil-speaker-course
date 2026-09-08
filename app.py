# REPARTITION PAR CATEGORIE ET TRANCHE D'AGE (ORDRE PAR ÂGE STRICT)
        with c_right:
            st.markdown("### 🏷️ Répartition par Catégorie (triée par âge)")
            
            if 'Catégorie' in df.columns:
                df_cat = df['Catégorie'].value_counts().reset_index()
                df_cat.columns = ['Code_Cat', 'Nombre']
                df_cat['Code_clean'] = df_cat['Code_Cat'].astype(str).str.strip().str.upper()
                
                # Filtrer sur les catégories reconnues et appliquer un ordre strict
                df_cat = df_cat[df_cat['Code_clean'].isin(ORDRE_CATEGORIES)].copy()
                df_cat['Code_clean'] = pd.Categorical(
                    df_cat['Code_clean'], 
                    categories=ORDRE_CATEGORIES, 
                    ordered=True
                )
                
                # Tri selon l'ordre strict des âges
                df_cat = df_cat.sort_values(by='Code_clean').reset_index(drop=True)
                df_cat['Catégorie & Plage d\'âge'] = df_cat['Code_clean'].apply(
                    lambda x: f"{x} - {CATEGORIES_AGE.get(str(x), 'Non spécifié')}"
                )
                
                # Graphique basé sur l'index ordonné (CA -> ES -> SE -> M0 -> M1...)
                chart_data = df_cat.set_index('Code_clean')[['Nombre']]
                st.bar_chart(chart_data)
                
                # Tableau synthétique
                st.dataframe(
                    df_cat[['Catégorie & Plage d\'âge', 'Nombre']], 
                    use_container_width=True, 
                    hide_index=True
                )