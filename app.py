# -------------------------------------------------------------
    # ONGLET 6 : SPONSORS & PARTENAIRES
    # -------------------------------------------------------------
    with tab_sponsors:
        st.subheader("🤝 Nos Partenaires Officiels")
        st.write("Un grand merci aux entreprises et institutions qui soutiennent les Foulées Raids Dingues !")
        
        st.markdown("---")
        
        # 1. SPONSORS ÉVÉNEMENTIELS
        st.markdown("### 🏆 Partenaires Événementiels")
        
        sponsors_evt = [
            ("L'Entrepote", "L'ENTREPOTE.png" if os.path.exists("L'ENTREPOTE.png") else "TC TRAITEUR.png", "150€ pour les dossards"),
            ("Intersport", "Intersport.png", "300€ de lots"),
            ("Pays de Fontenay", "PAYS DE FONTENAY.png", "Subvention de 400€"),
            ("La Cibulle", "LA CIBULLE.png" if os.path.exists("LA CIBULLE.png") else "LA CIBULL.png", "10% sur les fûts + 6 réglettes (lot)"),
            ("Vendée Marais Poitevin", "mvp.png", "Kit parcours orientation (lot)"),
            ("Valega", "VALEGA.png", "Massage de 45' (lot)"),
            ("CNAILS", "CNAILS.PNG" if os.path.exists("CNAILS.PNG") else "CNAILS.png", "Bon cadeau (lot)"),
            ("AXA", "AXA.png", "1 cafetière (lot)"),
            ("Bioporc", "BIOPORC.png", "3 terrines (lot)"),
            ("Les Pâtés de Lison", "PATES LISON.png", "3 lots de pâtes (lot)"),
            ("Vins Mercier", "VINS MERCIER.png", "3 bouteilles (lot)"),
            ("Hyper U", "HYPER U.png", "Paniers garnis (récompense course)"),
            ("Les Vergers de Vendée", "VERGERS DE VENDEE.png", "Paniers garnis (récompense course)"),
            ("Boucherie Gouin", "MAISON GOUIN.png", "Paniers garnis (récompense course)"),
            ("New Loc", "NEW LOC.png", "Lumière et groupe électrogène"),
            ("Édition du Chemin des Crêtes", "CHEMIN DES CRETES.png", "Livres (lot)"),
            ("Végétal 85", "VEGETAL85.png" if os.path.exists("VEGETAL85.png") else "VEGETAL 85.png", "Agapanthes (dotation coureurs)"),
            ("L'Escale des Ponts", "L'ESCALE.png", "Mise à disposition de l'emplacement")
        ]
        
        for sp_nom, sp_file, sp_desc in sponsors_evt:
            with st.container():
                c_logo, c_info = st.columns([1, 4])
                
                with c_logo:
                    if os.path.exists(sp_file):
                        st.image(sp_file, width=130)
                    else:
                        st.info(f"🏷️ **{sp_nom}**")
                        
                with c_info:
                    st.markdown(f"#### **{sp_nom}**")
                    if sp_desc:
                        st.markdown(f"##### 🎁 **Participation :** {sp_desc}")
                
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. SPONSORS ANNUELS
        st.markdown("### 🌟 Sponsors Annuels")
        sponsors_annuels = [
            ("BERNARD JOHANNE", "BERNARD JOHANNE.png"),
            ("BLANCHET ENERGIE", "BLANCHET ENERGIE.png"),
            ("BREMAUD", "BREMAUD.png"),
            ("CAJEV", "CAJEV.png"),
            ("LE GRAIN DE BLE", "LE GRAIN DE BLE.png"),
            ("MAISON BAUDRY", "MAISON BAUDRY.png"),
            ("MAISON GOUIN", "MAISON GOUIN.png"),
            ("ROBIN", "ROBIN.png"),
            ("SIGNALISATION 85", "SIGNALISATION 85.png"),
            ("SYMTA PIECES", "SYMTA PIECES.png"),
            ("VINCENDEAU AGENCEMENT", "VICENDEAU AGENCEMENT.png")
        ]
        
        cols_ann = st.columns(3)
        for idx, (sp_nom, sp_file) in enumerate(sponsors_annuels):
            with cols_ann[idx % 3]:
                if os.path.exists(sp_file):
                    st.image(sp_file, width=180)
                else:
                    st.info(f"🏷️ **{sp_nom}**")