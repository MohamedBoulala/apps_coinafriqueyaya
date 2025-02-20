import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import os
import matplotlib.pyplot as plt
import seaborn as sns

# CSS personnalisé pour une interface moderne
st.markdown(
    """
    <style>
    h1 {
        color: #4F8BF9;
        text-align: center;
        font-size: 3rem;
        margin-bottom: 30px;
    }
    h2 {
        color: #4F8BF9;
        font-size: 2rem;
        margin-bottom: 20px;
    }
    .stButton button {
        background-color: #4F8BF9;
        color: white;
        border-radius: 10px;
        padding: 15px 30px;
        font-size: 1.2rem;
        border: none;
        transition: background-color 0.3s ease;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #3a6bbf;
    }
    .stSidebar {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stMarkdown {
        font-size: 1.2rem;
        line-height: 1.6;
    }
    .stSelectbox, .stNumberInput {
        margin-bottom: 20px;
    }
    .stDataFrame {
        margin-top: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: black;
        color: white;
        text-align: center;
        padding: 15px;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .form-container {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Titre de l'application
st.title(" Coinafrica")

# Message de bienvenue
st.markdown("""
### Bienvenue sur l'Application Coinafrica !

Cette application vous permet de :
- *Scraper des données en temps réel* depuis le site Coinafrica.
- *Télécharger des données déjà scrapées* au format CSV.
- *Remplir des formulaires d'évaluation* directement dans l'application.

Utilisez la barre latérale pour sélectionner une catégorie et lancer le scraping. Vous pouvez également télécharger les données brutes et remplir les formulaires d'évaluation ci-dessous.
""")

# Fonction pour nettoyer les données
def clean_data(df):
    """
    Nettoie les données scrapées :
    - Supprime les lignes vides ou incomplètes.
    - Nettoie la colonne "Prix" (supprime "CFA" et convertit en nombre, gère les valeurs non numériques).
    - Nettoie la colonne "Adresse" (supprime les espaces superflus).
    - Nettoie la colonne "Image Lien" (s'assure que les URLs sont valides).
    """
    # Supprimer les lignes vides ou incomplètes
    df.dropna(inplace=True)

    # Nettoyer la colonne "Prix"
    if 'Prix' in df.columns:
        df['Prix'] = df['Prix'].apply(lambda x: clean_price(x))

    # Nettoyer la colonne "Adresse" (supprimer les espaces superflus)
    if 'Adresse' in df.columns:
        df['Adresse'] = df['Adresse'].str.strip()

    # Nettoyer la colonne "Image Lien" (s'assurer que les URLs sont valides)
    if 'Image Lien' in df.columns:
        df['Image Lien'] = df['Image Lien'].str.strip()

    return df

def clean_price(price):
    """
    Nettoie la valeur du prix :
    - Supprime "CFA" et les espaces.
    - Convertit en float si possible, sinon retourne 0.
    """
    try:
        # Supprimer "CFA" et les espaces
        cleaned_price = price.replace('CFA', '').replace(' ', '')
        # Convertir en float
        return float(cleaned_price)
    except ValueError:
        # Si la conversion échoue, retourner 0
        return 0.0

# Fonction pour scraper une page
def scrape_page(url, category):
    """
    Scrape les données d'une page spécifique.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie si la requête a réussi
        soup = BeautifulSoup(response.text, 'html.parser')
        annonces = soup.find_all('div', class_='col s6 m4 l3')  # Sélecteur pour les annonces
        data = []
        for annonce in annonces:
            try:
                # Extraire le titre (détails ou nom)
                title_element = annonce.find('p', class_="ad__card-description")
                title = title_element.text.strip() if title_element else "Titre non disponible"

                # Extraire le prix
                price_element = annonce.find('p', class_="ad__card-price")
                prix = price_element.text.strip() if price_element else "0 CFA"  # Valeur par défaut

                # Extraire l'adresse
                address_element = annonce.find('p', class_='ad__card-location')
                adresse = address_element.text.strip() if address_element else "Adresse non disponible"

                # Extraire le lien de l'image
                image_element = annonce.find('img', class_='ad__card-img')
                image_lien = image_element['src'] if image_element else "Lien d'image non disponible"

                # Ajouter les données à la liste
                data.append([title, prix, adresse, image_lien])
            except AttributeError as e:
                st.warning(f"Erreur lors de l'extraction d'une annonce : {e}")
                continue  # Passe à l'annonce suivante en cas d'erreur
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la requête HTTP : {e}")
        return []
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")
        return []

# Fonction pour scraper toutes les pages d'une catégorie
def scrape_category(base_url, category, num_pages):
    """
    Scrape toutes les pages d'une catégorie spécifique.
    """
    all_data = []
    for page in range(1, num_pages + 1):
        url = f"{base_url}?page={page}"  # Modifie selon la structure de l'URL
        st.write(f"Scraping page {page} de {category}...")
        page_data = scrape_page(url, category)
        all_data.extend(page_data)
    df = pd.DataFrame(all_data, columns=['Details/Nom', 'Prix', 'Adresse', 'Image Lien'])
    return clean_data(df)  # Nettoyer les données après le scraping

# URLs et nombre de pages pour chaque catégorie
categories = {
    "poules-lapins-et-pigeons": {
        "url": "https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons",
        "num_pages": 10  # 10 pages pour cette catégorie
    },
    "autres-animaux": {
        "url": "https://sn.coinafrique.com/categorie/autres-animaux",
        "num_pages": 6  # 6 pages pour cette catégorie
    }
}

# Barre latérale pour les paramètres de scraping
st.sidebar.markdown("### Paramètres de scraping")
category = st.sidebar.selectbox("Choisir une catégorie", list(categories.keys()))
num_pages = st.sidebar.number_input("Nombre de pages à scraper", min_value=1, max_value=20, value=1)

# Bouton pour lancer le scraping avec Beautiful Soup
if st.sidebar.button("Scraper les données en temps réel"):
    st.write(f"Scraping des données pour la catégorie : {category}...")
    df = scrape_category(categories[category]["url"], category, num_pages)
    if not df.empty:
        st.write("Données scrapées et nettoyées :")
        st.write(df)
        # === NOUVELLE SECTION : VISUALISATION DES DONNÉES SCRAPÉES EN DIRECT ===
        st.markdown("### Visualisation des données scrapées en direct")

        # Options de visualisation
        st.markdown("#### Choisissez un type de graphique")
        graph_type = st.selectbox(
            "Type de graphique",
            ["Histogramme des prix", "Nombre d'annonces par catégorie", "Nuage de points (Prix vs Adresse)"]
        )

        # Afficher le graphique sélectionné
        if graph_type == "Histogramme des prix":
            st.markdown("#### Histogramme des prix")
            fig, ax = plt.subplots()
            sns.histplot(df['Prix'], bins=20, kde=True, ax=ax)
            ax.set_xlabel("Prix (CFA)")
            ax.set_ylabel("Nombre d'annonces")
            ax.set_title("Distribution des prix")
            st.pyplot(fig)

        elif graph_type == "Nombre d'annonces par catégorie":
            st.markdown("#### Nombre d'annonces par catégorie")
            fig, ax = plt.subplots()
            df['Catégorie'].value_counts().plot(kind='bar', ax=ax)
            ax.set_xlabel("Catégorie")
            ax.set_ylabel("Nombre d'annonces")
            ax.set_title("Nombre d'annonces par catégorie")
            st.pyplot(fig)

        elif graph_type == "Nuage de points (Prix vs Adresse)":
            st.markdown("#### Nuage de points : Prix vs Adresse")
            fig, ax = plt.subplots()
            sns.scatterplot(data=df, x='Prix', y='Adresse', ax=ax)
            ax.set_xlabel("Prix (CFA)")
            ax.set_ylabel("Adresse")
            ax.set_title("Relation entre le prix et l'adresse")
            st.pyplot(fig)

        # === FIN DE LA NOUVELLE SECTION ===

        # Télécharger les données scrapées en CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les données nettoyées en CSV",
            data=csv,
            file_name=f"{category}_scraped_data_clean.csv",
            mime="text/csv"
        )
    else:
        st.warning("Aucune donnée n'a été récupérée. Vérifiez les erreurs ci-dessus.")

# Section pour télécharger les données déjà scrapées (Web Scraper)
st.markdown("### Télécharger les données brutes (Web Scraper)")
col1, col2 = st.columns(2)  # Utilisation de colonnes pour aligner les boutons

with col1:
    if st.button("Télécharger les données brutes (Poules, Lapins et Pigeons)"):
        try:
            # Lire le fichier CSV brut pour "poules-lapins-et-pigeons"
            df_raw_poules = pd.read_csv("poules-lapins-et-pigeons_raw.csv")
            st.write("Données brutes (Poules, Lapins et Pigeons):")
            st.write(df_raw_poules)

            # Télécharger le fichier CSV
            st.download_button(
                label="📥 Télécharger CSV",
                data=df_raw_poules.to_csv(index=False),
                file_name="poules-lapins-et-pigeons_raw.csv",
                mime="text/csv"
            )
        except FileNotFoundError:
            st.error("Fichier introuvable : poules-lapins-et-pigeons_raw.csv")
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")

with col2:
    if st.button("Télécharger les données brutes (Autres Animaux)"):
        try:
            # Lire le fichier CSV brut pour "autres-animaux"
            df_raw_autres = pd.read_csv("autres-animaux_raw.csv")
            st.write("Données brutes (Autres Animaux):")
            st.write(df_raw_autres)

            # Télécharger le fichier CSV
            st.download_button(
                label="📥 Télécharger CSV",
                data=df_raw_autres.to_csv(index=False),
                file_name="autres-animaux_raw.csv",
                mime="text/csv"
            )
        except FileNotFoundError:
            st.error("Fichier introuvable : autres-animaux_raw.csv")
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
# Section pour les formulaires d'évaluation
st.markdown("### Formulaires d'évaluation")
form1, form2 = st.columns(2)  # Deux colonnes pour les formulaires

with form1:
    st.markdown("#### Formulaire Kobo Collect")
    if st.button("Afficher le formulaire Kobo Collect"):
        st.write("""
        <iframe src="https://ee.kobotoolbox.org/x/LSJggN73" width="800" height="600"></iframe>
        """, unsafe_allow_html=True)

with form2:
    st.markdown("#### Formulaire Google Forms")
    if st.button("Afficher le formulaire Google Forms"):
        st.write("""
        <iframe src="https://forms.gle/nu6vHtmrJYsomtDv8" width="100%" height="500px"></iframe>
        """, unsafe_allow_html=True)

# Pied de page
st.markdown(
    """
    <div class="footer">
        Presented by YAYA BALARABE
    </div>
    """,
    unsafe_allow_html=True
)