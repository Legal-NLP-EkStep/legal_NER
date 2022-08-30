######### Definitions of spacy components needed for legal NER
import spacy
from spacy import displacy
import re
from data_preparation import seperate_and_clean_preamble,get_text_from_indiankanoon_url
from spacy.tokens import Span
import time


def extract_entities_from_judgment_text(txt,legal_nlp):
    ######### Seperate Preamble and judgment text
    seperation_start_time = time.time()
    nlp_preamble_splitting = spacy.load('en_core_web_sm')
    preamble_text,preamble_end= seperate_and_clean_preamble(txt,nlp_preamble_splitting)
    print("Seperating Preamble took " + str(time.time() - seperation_start_time))

    ########## process main judgement text
    judgement_start_time = time.time()
    judgement_text=txt[preamble_end:]
    #####  replace new lines in middle of sentence with spaces.
    judgement_text = re.sub(r'(\w[ -]*)(\n+)', r'\1 ', judgement_text)
    doc_judgment=legal_nlp(judgement_text)
    print("Creating doc for jdgement  took " + str(time.time() - judgement_start_time))

    ######### process preamable
    preamble_start_time = time.time()
    doc_preamble = legal_nlp(preamble_text)
    print("Creating doc for preamble  took " + str(time.time() - preamble_start_time))

    ######### Combine preamble doc & judgement doc
    combining_start_time = time.time()
    combined_doc = spacy.tokens.Doc.from_docs([doc_preamble, doc_judgment])
    print("Combining took " + str(time.time() - combining_start_time))

    return combined_doc

if __name__ == "__main__":
    indiankanoon_url = 'https://indiankanoon.org/doc/150051/'
    #indiankanoon_url = 'https://indiankanoon.org/doc/639803/'

    txt = get_text_from_indiankanoon_url(indiankanoon_url)

    legal_nlp = spacy.load('/Users/prathamesh/tw_projects/OpenNyAI/data/NER/train/exp_NO4/trf/Combined/model-best') ## path of trained model files
    ########## Extract Entities
    combined_doc = extract_entities_from_judgment_text(txt,legal_nlp)

    ########### show the entities
    extracted_ent_labels = list(set([i.label_ for i in combined_doc.ents]))
    colors = {'COURT':"#bbabf2",'PETITIONER': "#f570ea", "RESPONDENT": "#cdee81",'JUDGE':"#fdd8a5","LAWYER":"#f9d380",
              'WITNESS':"violet","STATUTE":"#faea99","PROVISION":"yellow",'CASE_NUMBER':"#fbb1cf","PRECEDENT":"#fad6d6",
              'POLICE_STATION':"#b1ecf7",'OTHER_PERSON':"#b0f6a2"}
    options = {"ents": extracted_ent_labels, "colors": colors}


    displacy.serve(combined_doc, style='ent',port=8080,options=options)
