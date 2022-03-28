######### Definitions of spacy components needed for legal NER
import spacy
from spacy import displacy
import re
from data_preparation import seperate_and_clean_preamble
from judgment_text_pipeline import get_judgment_text_pipeline
from preamble_pipeline import get_spacy_nlp_pipeline_for_preamble
from data_preparation import get_text_from_indiankanoon_url
from spacy.tokens import Span
import time


def extract_entities_from_judgment_text(txt,nlp_preamble_splitting , nlp_judgment,nlp_preamble):
    ######### Seperate Preamble and judgment text
    seperation_start_time = time.time()
    preamble_text,preamble_end= seperate_and_clean_preamble(txt,nlp_preamble_splitting)
    print("Seperating Preamble took " + str(time.time() - seperation_start_time))

    ########## process main judgement text
    judgement_start_time = time.time()
    judgement_text=txt[preamble_end:]
    judgement_text = re.sub(r'([^.\"\?])\n+ *', r'\1 ', judgement_text)
    doc_judgment=nlp_judgment(judgement_text)
    print("Creating doc for jdgement  took " + str(time.time() - judgement_start_time))

    ######### process preamable
    preamble_start_time = time.time()
    doc_preamble = nlp_preamble(preamble_text)
    print("Creating doc for preamble  took " + str(time.time() - preamble_start_time))

    ######### Combine preamble doc & judgement doc
    combining_start_time = time.time()
    combined_doc = spacy.tokens.Doc.from_docs([doc_preamble, doc_judgment])
    print("Combining took " + str(time.time() - combining_start_time))

    return combined_doc

def create_spacy_pipelines():
    ####### Pipeline for main judgement text
    nlp_judgment = get_judgment_text_pipeline()

    preamble_entities_list = ['COURT','PETITIONER','RESPONDENT','LAWYER','JUDGE']
    for preamble_entity in preamble_entities_list:
        nlp_judgment.vocab.strings.add(preamble_entity)

    ###### Pipeline for preamble
    nlp_preamble = get_spacy_nlp_pipeline_for_preamble(nlp_judgment.vocab)
    nlp_preamble.add_pipe("extract_preamble_entities", after="ner")

    ###### Pipeline for preamble splitting
    nlp_preamble_splitting = get_spacy_nlp_pipeline_for_preamble(nlp_judgment.vocab)
    return nlp_preamble_splitting,nlp_preamble,nlp_judgment

if __name__ == "__main__":
    #indiankanoon_url = 'https://indiankanoon.org/doc/768571/'
    indiankanoon_url = 'https://indiankanoon.org/doc/102783788/'
    txt = get_text_from_indiankanoon_url(indiankanoon_url)

    ######## create spacy pipelines needed for preamble & main text
    start_time = time.time()
    nlp_preamble_splitting,nlp_preamble,nlp_judgment = create_spacy_pipelines()
    print("Creation of pipelines took " + str(time.time() - start_time))

    ########## Extract Entities
    combined_doc = extract_entities_from_judgment_text(txt,nlp_preamble_splitting , nlp_judgment,nlp_preamble)

    ########### show the entities
    extracted_ent_labels = list(set([i.label_ for i in combined_doc.ents]))
    colors = {'COURT':"#bbabf2",'PETITIONER': "#f570ea", "RESPONDENT": "#cdee81",'JUDGE':"#fdd8a5","LAWYER":"#f9d380",
              'WITNESS':"violet","STATUTE":"#faea99","PROVISION":"yellow",'CASE_NUMBER':"#fbb1cf","PRECEDENT":"#fad6d6",
              'POLICE_STATION':"#b1ecf7",'OTHER_ORG':"#b0f6a2"}
    options = {"ents": extracted_ent_labels, "colors": colors}

    displacy.serve(combined_doc, style='ent',port=8080,options=options)
