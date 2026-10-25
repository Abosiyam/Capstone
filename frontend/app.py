# ============================================================================
# Section 2 – Basket & Recommendations
# ============================================================================
elif section == t['basket']:
    st.header(t['basket'])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛒 Your Basket")
        
        import json
        from pathlib import Path
        catalog_path = Path(__file__).parent.parent / 'artifacts' / 'product_catalog.json'
        catalog = {}
        if catalog_path.exists():
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
                
        product_options = {f"{v['description']} ({k})": k for k, v in catalog.items()}
        
        # Default selection (84997C)
        default_label = [label for label, code in product_options.items() if code == "84997C"]
        
        selected_products = st.multiselect(
            "Select products to add to your basket:",
            options=list(product_options.keys()),
            default=default_label
        )
        
        n_recs = st.slider("Number of recommendations", 1, 10, 5)

        if st.button(t['get_recommendations'], type="primary"):
            # Convert selected product names back to StockCodes
            basket = [product_options[p] for p in selected_products if p in product_options]
            
            if not basket:
                st.warning("Please select at least one product first.")
            else:
                with st.spinner("Fetching recommendations from API (may take 30s if server is asleep)..."):
                    result = call_api("/recommend", "POST", {"basket": basket, "n": n_recs})
                
                if "error" in result:
                    st.error(f"API Error: {result['error']}. Please refresh and try again.")
                else:
                    st.session_state.recs = result

    with col2:
        st.subheader("💡 " + t['recommendations'])
        
        # Check if we have recommendations in session state
        if "recs" in st.session_state and st.session_state.recs is not None:
            result = st.session_state.recs
            strategy = result.get('strategy')
            st.info(f"Strategy: **{strategy}**")

            recs = result.get('recommendations', [])
            if not recs:
                st.warning(result.get('message', 'No recommendations available for this basket.'))
            else:
                for rec in recs:
                    with st.container():
                        st.markdown(f"### 📦 `{rec['item']}`")
                        st.markdown(f"**Lift:** {rec['lift']:.2f} | **Confidence:** {rec['confidence']:.2%}")
                        st.caption(f"Because you added: {', '.join(rec['because'])}")
                        st.markdown("---")
        else:
            st.info("Select products and click 'Get Recommendations' to see results.")