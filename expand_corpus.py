from pathlib import Path

CORPUS_DIR = Path('docs/corpus')

delivery_extra = """
## 7. Livraison en zones rurales / Rural Delivery
Pour les codes postaux commençant par G, J, ou X, les livraisons peuvent prendre jusqu'à 7 jours ouvrables. Un supplément de 5 $ s'applique pour les adresses situées à plus de 50 km d'un centre de distribution.
## 8. Emballage écologique / Eco-friendly Packaging
Tous nos colis sont emballés dans des matériaux 100% recyclés. Si vous recevez des produits frais, ils sont transportés dans des sacs isothermes biodégradables. Veuillez laisser vos sacs isothermes à votre livreur lors de la prochaine commande.
## 9. Échec de livraison / Failed Delivery
Si le livreur ne peut pas remettre le colis (adresse incorrecte, absence), un avis de passage sera laissé. Le colis sera retourné à notre entrepôt. Des frais de réexpédition de 12 $ seront facturés pour un nouvel envoi.
"""

returns_extra = """
## 7. Articles en solde / Sale Items
Les articles achetés en solde (réduction de 50% ou plus) ne sont pas admissibles à un remboursement, mais peuvent être échangés contre un crédit en magasin dans les 14 jours.
## 8. Produits électroniques / Electronics
Les articles électroniques (thermomètres, balances de cuisine) doivent être retournés non ouverts. Si l'emballage est scellé par le fabricant et a été ouvert, des frais de restocking de 15% s'appliquent.
## 9. Retours pendant les fêtes / Holiday Returns
Pour les achats effectués entre le 1er novembre et le 24 décembre, la période de retour est prolongée jusqu'au 15 janvier de l'année suivante, sur présentation du reçu original.
"""

allergens_extra = """
## 7. Contamination croisée / Cross-Contamination
Nos installations manipulent des arachides, des noix, du lait, du blé, du soja, des œufs, des crustacés et du sésame. Bien que nous prenions des mesures strictes de nettoyage, nous ne pouvons pas garantir l'absence totale de traces.
## 8. Produits casher et halal / Kosher and Halal
Les produits certifiés Casher et Halal sont clairement identifiés sur notre site web avec les logos correspondants. Ces produits proviennent de fournisseurs certifiés indépendants.
## 9. Gluten et régime sans allergènes / Gluten-Free
Les produits étiquetés "sans gluten" contiennent moins de 20 parties par million (ppm) de gluten, conformément aux normes de Santé Canada.
"""

loyalty_extra = """
## 7. Anniversaire du client / Customer Birthday
Les membres reçoivent un coupon de 10 $ valide pendant le mois de leur anniversaire. Ce coupon ne peut pas être combiné avec d'autres promotions.
## 8. Parrainage / Referral Program
Pour chaque nouvel ami parrainé qui passe une première commande de 50 $ ou plus, vous recevrez 2 000 points (l'équivalent de 20 $ de réduction) et votre ami recevra 15 $ de réduction sur sa première commande.
## 9. Expiration des niveaux / Tier Expiration
Pour maintenir votre statut Or ou Platine, vous devez effectuer au moins 12 commandes par année civile. Si ce seuil n'est pas atteint, votre compte sera rétrogradé au niveau inférieur au début de la nouvelle année.
"""

privacy_extra = """
## 8. Cookies et traceurs / Cookies and Trackers
Nous utilisons des cookies essentiels pour le fonctionnement du site (panier, connexion) et des cookies analytiques (Google Analytics) pour comprendre comment nos clients naviguent. Vous pouvez désactiver les cookies analytiques dans les paramètres de votre navigateur sans affecter l'expérience d'achat.
## 9. Conservation des données / Data Retention
Les données de transaction sont conservées pendant 7 ans pour des raisons fiscales et comptables. Les profils clients inactifs depuis plus de 3 ans sont anonymisés automatiquement.
## 10. Transfert international / International Transfer
Vos données sont hébergées sur des serveurs sécurisés au Canada. Dans le cas d'un service tiers (comme le traitement des paiements), nous nous assurons que le fournisseur respecte les normes de protection des données équivalentes à la Loi 25 du Québec.
"""

def expand():
    files = {
        'delivery.md': delivery_extra,
        'returns.md': returns_extra,
        'allergens.md': allergens_extra,
        'loyalty.md': loyalty_extra,
        'privacy.md': privacy_extra,
    }
    
    for filename, extra_text in files.items():
        filepath = CORPUS_DIR / filename
        if filepath.exists():
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(extra_text)
            print(f"✅ Expanded {filename}")
        else:
            print(f"⚠️ {filename} not found!")
            
    print("\n✅ Corpus expansion complete!")

if __name__ == "__main__":
    expand()