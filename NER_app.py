import streamlit as st
from spacy import displacy

from legal_ner import create_spacy_pipelines, extract_entities_from_judgment_text
from data_preparation import get_text_from_indiankanoon_url

st.title("Legal Named Entity Recognizer")
st.header("Extacts Entities from Indian Court Judgement text.")


indiankanoon_url = st.text_input('Paste IndianKanoon Link below and press Enter. E.g. https://indiankanoon.org/doc/41737003/','')

if indiankanoon_url!='':
    nlp_preamble_splitting, nlp_preamble, nlp_judgment = create_spacy_pipelines()
    txt = get_text_from_indiankanoon_url(indiankanoon_url)
    doc = extract_entities_from_judgment_text(txt,nlp_preamble_splitting , nlp_judgment,nlp_preamble)

    extracted_ent_labels = list(set([i.label_ for i in doc.ents]))
    colors = {'COURT': "#bbabf2", 'PETITIONER': "#f570ea", "RESPONDENT": "#cdee81", 'JUDGE': "#fdd8a5", "LAWYER": "#f9d380",
              'WITNESS': "violet", "STATUTE": "#faea99", "PROVISION": "yellow", 'CASE_NUMBER': "#fbb1cf",
              "PRECEDENT": "#fad6d6",
              'POLICE_STATION': "#b1ecf7", 'OTHER_ORG': "#b0f6a2"}
    options = {"ents": extracted_ent_labels, "colors": colors}
    st.header("Entity visualizer")

    ent_html = displacy.render(doc, style="ent", jupyter=False,options=options)

    st.markdown(ent_html, unsafe_allow_html=True)
