import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import cm
from datetime import datetime
import io

# Nederlandse CO₂-emissiefactoren 2024 (bron: CO2emissiefactoren.nl)
EMISSIEFACTOREN = {
    'Aardgas (m³)': 2.085,  # kg CO₂-eq per m³
    'Elektriciteit - Grijze stroom (kWh)': 0.536,  # kg CO₂-eq per kWh
    'Elektriciteit - Groene stroom (kWh)': 0.000,  # kg CO₂-eq per kWh
    'Diesel (liter)': 3.256,  # kg CO₂-eq per liter
    'Benzine (liter)': 2.821  # kg CO₂-eq per liter
}

def bereken_emissies(gas_m3, elektra_kwh, stroom_type, diesel_liter):
    """Bereken CO₂-emissies op basis van verbruik"""
    emissies = {}
    
    if gas_m3 > 0:
        emissies['Aardgas'] = gas_m3 * EMISSIEFACTOREN['Aardgas (m³)']
    
    if elektra_kwh > 0:
        factor_key = f'Elektriciteit - {stroom_type} (kWh)'
        emissies['Elektriciteit'] = elektra_kwh * EMISSIEFACTOREN[factor_key]
    
    if diesel_liter > 0:
        emissies['Diesel'] = diesel_liter * EMISSIEFACTOREN['Diesel (liter)']
    
    return emissies

def maak_staafdiagram(emissies_data):
    """Maak een staafdiagram van de emissies"""
    if not emissies_data
        return None
    
    categorieen = list(emissies_data.keys())
    waarden = list(emissies_data.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=categorieen,
            y=waarden,
            marker_color=['#21808D', '#A87B2F', '#C0152F'],
            text=[f'{w:.1f} kg' for w in waarden],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='CO₂-emissies per categorie',
        xaxis_title='Energiedrager',
        yaxis_title='CO₂-emissies (kg CO₂-eq)',
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_yaxes(gridcolor='lightgray')
    
    return fig

def genereer_pdf(emissies_data, verbruik_data, totaal_emissie, stroom_type):
    """Genereer een PDF-rapport met de resultaten"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Styling
    styles = getSampleStyleSheet()
    titel_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#21808D'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    subtitel_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#134252'),
        spaceAfter=12
    )
    
    # Content elementen
    story = []
    
    # Titel
    story.append(Paragraph('CO₂-emissies Rapport', titel_style))
    story.append(Paragraph(f'Gegenereerd op: {datetime.now().strftime("%d-%m-%Y om %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Verbruiksoverzicht
    story.append(Paragraph('Verbruiksoverzicht', subtitel_style))
    
    verbruik_tabel_data = [
        ['Energiedrager', 'Verbruik', 'Eenheid'],
        ['Aardgas', f"{verbruik_data['gas']:.2f}", 'm³'],
        ['Elektriciteit', f"{verbruik_data['elektra']:.2f}", 'kWh'],
        ['Stroomtype', stroom_type, ''],
        ['Diesel', f"{verbruik_data['diesel']:.2f}", 'liter']
    ]
    
    verbruik_tabel = Table(verbruik_tabel_data, colWidths=[6*cm, 4*cm, 3*cm])
    verbruik_tabel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#21808D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(verbruik_tabel)
    story.append(Spacer(1, 1*cm))
    
    # Emissies overzicht
    story.append(Paragraph('CO₂-emissies per categorie', subtitel_style))
    
    emissie_tabel_data = [['Categorie', 'CO₂-emissies (kg CO₂-eq)', 'Percentage']]
    
    for categorie, emissie in emissies_data.items():
        percentage = (emissie / totaal_emissie * 100) if totaal_emissie > 0 else 0
        emissie_tabel_data.append([
            categorie,
            f'{emissie:.2f}',
            f'{percentage:.1f}%'
        ])
    
    # Totaal rij
    emissie_tabel_data.append(['TOTAAL', f'{totaal_emissie:.2f}', '100%'])
    
    emissie_tabel = Table(emissie_tabel_data, colWidths=[6*cm, 5*cm, 3*cm])
    emissie_tabel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#21808D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#A7A9A9')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(emissie_tabel)
    story.append(Spacer(1, 1*cm))
    
    # Emissiefactoren referentie
    story.append(Paragraph('Gebruikte emissiefactoren (2024)', subtitel_style))
    story.append(Paragraph(
        'Bron: CO2emissiefactoren.nl - Officiële Nederlandse emissiefactoren',
        styles['Italic']
    ))
    story.append(Spacer(1, 0.5*cm))
    
    factoren_tabel_data = [['Energiedrager', 'Emissiefactor', 'Eenheid']]
    for naam, factor in EMISSIEFACTOREN.items():
        factoren_tabel_data.append([naam, f'{factor:.3f}', 'kg CO₂-eq'])
    
    factoren_tabel = Table(factoren_tabel_data, colWidths=[8*cm, 3*cm, 3*cm])
    factoren_tabel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#626C71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(factoren_tabel)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Streamlit App
def main():
    st.set_page_config(
        page_title='CO₂-emissies Calculator',
        page_icon='🌍',
        layout='centered'
    )
    
    st.title('🌍 CO₂-emissies Calculator')
    st.markdown('**Bereken je CO₂-uitstoot op basis van Nederlandse emissiefactoren 2024**')
    st.markdown('---')
    
    # Sidebar met info
    with st.sidebar:
        st.header('ℹ️ Informatie')
        st.markdown("""
        Deze calculator gebruikt de officiële Nederlandse CO₂-emissiefactoren 
        uit 2024 zoals gepubliceerd op **CO2emissiefactoren.nl**.
        
        **Emissiefactoren:**
        - Aardgas: 2,085 kg CO₂-eq/m³
        - Grijze stroom: 0,536 kg CO₂-eq/kWh
        - Groene stroom: 0,000 kg CO₂-eq/kWh
        - Diesel: 3,256 kg CO₂-eq/liter
        - Benzine: 2,821 kg CO₂-eq/liter
        """)
    
    # Input sectie
    st.header('📊 Voer je verbruik in')
    
    col1, col2 = st.columns(2)
    
    with col1:
        gas_verbruik = st.number_input(
            'Aardgas verbruik (m³)',
            min_value=0.0,
            value=0.0,
            step=10.0,
            format='%.2f',
            help='Voer het gasverbruik in kubieke meters in'
        )
        
        elektra_verbruik = st.number_input(
            'Elektriciteit verbruik (kWh)',
            min_value=0.0,
            value=0.0,
            step=50.0,
            format='%.2f',
            help='Voer het elektriciteitsverbruik in kilowattuur in'
        )
    
    with col2:
        stroom_type = st.selectbox(
            'Type elektriciteit',
            options=['Grijze stroom', 'Groene stroom'],
            help='Selecteer of je grijze of groene stroom gebruikt'
        )
        
        diesel_verbruik = st.number_input(
            'Diesel verbruik (liter)',
            min_value=0.0,
            value=0.0,
            step=10.0,
            format='%.2f',
            help='Voer het dieselverbruik in liters in'
        )
    
    st.markdown('---')
    
    # Bereken knop
    if st.button('🔄 Bereken CO₂-emissies', type='primary', use_container_width=True):
        if gas_verbruik == 0 and elektra_verbruik == 0 and diesel_verbruik == 0:
            st.warning('⚠️ Voer minimaal één verbruikswaarde in om te berekenen.')
        else:
            # Bereken emissies
            emissies = bereken_emissies(gas_verbruik, elektra_verbruik, stroom_type, diesel_verbruik)
            totaal = sum(emissies.values())
            
            # Opslaan in session state
            st.session_state['emissies'] = emissies
            st.session_state['totaal'] = totaal
            st.session_state['verbruik'] = {
                'gas': gas_verbruik,
                'elektra': elektra_verbruik,
                'diesel': diesel_verbruik
            }
            st.session_state['stroom_type'] = stroom_type
    
    # Toon resultaten als beschikbaar
    if 'emissies' in st.session_state:
        st.markdown('---')
        st.header('📈 Resultaten')
        
        # Totaal emissie
        st.metric(
            label='Totale CO₂-emissies',
            value=f"{st.session_state['totaal']:.2f} kg CO₂-eq",
            delta=None
        )
        
        st.markdown('### Emissies per categorie')
        
        # Tabel met details
        emissie_df = pd.DataFrame({
            'Categorie': list(st.session_state['emissies'].keys()),
            'CO₂-emissies (kg)': [f"{v:.2f}" for v in st.session_state['emissies'].values()],
            'Percentage': [f"{(v/st.session_state['totaal']*100):.1f}%" 
                          for v in st.session_state['emissies'].values()]
        })
        
        st.dataframe(emissie_df, use_container_width=True, hide_index=True)
        
        # Staafdiagram
        fig = maak_staafdiagram(st.session_state['emissies'])
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('---')
        
        # Download PDF knop
        st.header('📄 Download rapport')
        
        pdf_buffer = genereer_pdf(
            st.session_state['emissies'],
            st.session_state['verbruik'],
            st.session_state['totaal'],
            st.session_state['stroom_type']
        )
        
        st.download_button(
            label='📥 Download Rapport (PDF)',
            data=pdf_buffer,
            file_name=f'CO2_rapport_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mime='application/pdf',
            type='primary',
            use_container_width=True
        )
        
        st.success('✅ Rapport is klaar om te downloaden!')

if __name__ == '__main__':
    main()
