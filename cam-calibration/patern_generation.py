from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

def generer_damier_pdf(nom_fichier, taille_case_mm, lignes, colonnes):
    # Format A4 en mode paysage (297 mm x 210 mm)
    largeur_page, hauteur_page = landscape(A4)
    c = canvas.Canvas(nom_fichier, pagesize=landscape(A4))
    
    # Conversion de la taille des cases en points (l'unité par défaut de reportlab)
    taille_case = taille_case_mm * mm
    
    # Calcul des dimensions totales du damier
    largeur_damier = colonnes * taille_case
    hauteur_damier = lignes * taille_case
    
    # Calcul des marges pour centrer le damier sur la page
    marge_x = (largeur_page - largeur_damier) / 2.0
    marge_y = (hauteur_page - hauteur_damier) / 2.0
    
    # Définir la couleur de remplissage sur noir
    c.setFillColorRGB(0, 0, 0)
    
    # Dessiner le damier
    for ligne in range(lignes):
        for colonne in range(colonnes):
            # On alterne les cases noires et blanches
            if (ligne + colonne) % 2 == 1:
                x = marge_x + colonne * taille_case
                y = marge_y + ligne * taille_case
                c.rect(x, y, taille_case, taille_case, fill=1, stroke=0)
                
    # Sauvegarder la page et le fichier PDF
    c.showPage()
    c.save()
    print(f"Le fichier '{nom_fichier}' a été généré avec succès !")

# Paramètres correspondants à ton code (7x6 coins internes = damier de 8x7 cases)
generer_damier_pdf(
    nom_fichier="patern.pdf",
    taille_case_mm=25, 
    lignes=7, 
    colonnes=8
)