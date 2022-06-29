import spacy
import re
from spacy.pipeline import Sentencizer
from typing import Optional, List, Callable
from spacy.language import Language
from spacy.tokens import Span

@Language.factory(
    "my_sentencizer",
    assigns=["token.is_sent_start", "doc.sents"],
    default_config={"punct_chars": None, "overwrite": False, "scorer": {"@scorers": "spacy.senter_scorer.v1"}},
    default_score_weights={"sents_f": 1.0, "sents_p": 0.0, "sents_r": 0.0},
)
def make_sentencizer(
    nlp: Language,
    name: str,
    punct_chars: Optional[List[str]],
    overwrite: bool,
    scorer: Optional[Callable],):
    return mySentencizer(name, punct_chars=punct_chars, overwrite=overwrite, scorer=scorer)


class mySentencizer(Sentencizer):
    def predict(self, docs):
        """Apply the pipe to a batch of docs, without modifying them.

        docs (Iterable[Doc]): The documents to predict.
        RETURNS: The predictions for each document.
        """
        if not any(len(doc) for doc in docs):
            # Handle cases where there are no tokens in any docs.
            guesses = [[] for doc in docs]
            return guesses
        guesses = []
        for doc in docs:
            doc_guesses = [False] * len(doc)
            if len(doc) > 0:
                start = 0
                seen_period = False
                doc_guesses[0] = True
                for i, token in enumerate(doc):
                    is_in_punct_chars = bool(re.match(r'^\n\s*$',token.text)) ####### hardcoded punctuations to newline characters
                    if seen_period and not is_in_punct_chars:
                        doc_guesses[start] = True
                        start = token.i
                        seen_period = False
                    elif is_in_punct_chars:
                        seen_period = True
                if start < len(doc):
                    doc_guesses[start] = True
            guesses.append(doc_guesses)
        return guesses

def get_spacy_nlp_pipeline_for_preamble(vocab,model_name="en_core_web_sm"):
    ########## Creates spacy nlp pipeline for Judgment Preamble. the sentence splitting is done on new lines.
    nlp = spacy.load(model_name,vocab=vocab,exclude=['ner'])
    nlp.max_length = 30000000
    ########### Split sentences on new lines for preamble
    nlp.add_pipe("my_sentencizer", before='parser')
    return nlp


def extract_proper_nouns(sent,keywords):
    proper_nouns_list = []
    current_proper_noun_start = None
    for token in sent:
        if token.pos_=="PROPN" and token.lower_ not in keywords:
            if current_proper_noun_start is None:
                current_proper_noun_start = token.i
        elif current_proper_noun_start is not None and ((token.pos_ != 'ADP' and not token.is_punct) or token.lower_ in keywords):
            proper_nouns_list.append(sent.doc[current_proper_noun_start:token.i])
            current_proper_noun_start = None

    return proper_nouns_list

def match_span_with_keyword(span,keyword_dict):
    ########## matches the keywords in the given input span which is part of input sent
    span_label = None
    ##### check if court
    if span.text.lower().__contains__('court'):
        span_label ='COURT'
    else:
        ######check for judge patterns
        last_non_space_token = []
        if len([token for token in span if token.lower_ in keyword_dict['judge_keywords']]) > 0 or span.text.strip().endswith('J.'):
            span_label='JUDGE'
        else:
            ############# check for lawyer pattern
            if len([token for token in span if token.lower_ in keyword_dict['lawyer_keywords']]) > 0:
                span_label='LAWYER'
            ##### check if the "for" keyword is present after petitioner or respondent keyword
            elif any([span.text.lower().find('for '+i)>=0 for i in keyword_dict['petitioner_keywords']+keyword_dict['respondent_keywords']]):
                span_label = 'LAWYER'
            else:
                ########## check for petitioner
                if len([token for token in span if token.lower_ in keyword_dict['petitioner_keywords']]) > 0:
                    span_label='PETITIONER'
                elif len([token for token in span if token.lower_ in keyword_dict['respondent_keywords']]) > 0:
                    span_label='RESPONDENT'
    return span_label


def validate_label(text_to_evaluate, sent_label):
    ########## checks to validate the chunk text
    valid_label= True
    if sent_label=='COURT' and not text_to_evaluate.lower().__contains__('court'):
        valid_label = False
    else:
        #### there should be atleast two characters
        if len([ele for ele in text_to_evaluate if ele.isalpha()]) <=2:
            valid_label = False
    return valid_label


def add_chunk_entities(new_ents, block_ents, label_for_unknown_ents, doc, block_start_with_sequence_number, label_indicated_by_previous_block, block_label_carry_forward_over_block_cnt, block_in_sequence, previous_block_sequence_number):
    sequence_number_suggested_next_block_label = None
    entities_cnt_added_from_current_chunk = 0
    for block_ent in block_ents:
        entity_label = block_ent['label']
        if entity_label != 'UNKNOWN':
            final_entity_label = entity_label
        elif entity_label == 'UNKNOWN' and label_for_unknown_ents is not None:
            final_entity_label = label_for_unknown_ents
        else:
            final_entity_label = None

        if final_entity_label is not None:
            valid_label = validate_label(doc[block_ent['start']:block_ent['end']].text.lower(), final_entity_label)
            if valid_label:
                new_ent = Span(doc, block_ent['start'], block_ent['end'], label=final_entity_label)
                new_ents.append(new_ent)
                entities_cnt_added_from_current_chunk +=1
                if final_entity_label in ['PETITIONER', 'RESPONDENT']:
                    if block_start_with_sequence_number and final_entity_label == label_indicated_by_previous_block and block_in_sequence:
                        sequence_number_suggested_next_block_label = final_entity_label
                    else:
                        sequence_number_suggested_next_block_label = None
                    ##### choose the first entity of the block for PETITIONER & RESPONDENT
                    break
    if (entities_cnt_added_from_current_chunk ==0 or final_entity_label == label_indicated_by_previous_block) and block_label_carry_forward_over_block_cnt < 4 :
        sequence_number_suggested_next_block_label = label_indicated_by_previous_block
        if label_indicated_by_previous_block is not None:
            block_label_carry_forward_over_block_cnt +=1
    else:
        # if block_label_carry_forward_over_block_cnt >= 4:
        previous_block_sequence_number = 0
        block_label_carry_forward_over_block_cnt = 0
        sequence_number_suggested_next_block_label = None

    return sequence_number_suggested_next_block_label, block_label_carry_forward_over_block_cnt, previous_block_sequence_number

def get_next_block_label(keyword_suggested_next_block_label,sequence_number_suggested_next_block_label):
    if keyword_suggested_next_block_label:
        next_block_label = keyword_suggested_next_block_label
    elif sequence_number_suggested_next_block_label:
        next_block_label = sequence_number_suggested_next_block_label
    else:
        next_block_label = None
    return next_block_label




def check_if_sentence_is_at_end_of_block(text):
    ########## check if sentence is ending with multiple new lines or the keywords that define end of block
    next_block_label = None
    current_block_end= False
    if re.match(r'^\s*Between *\:?\s*$', text) or re.match(r'^\s*BETWEEN *\:?\s*$', text) or\
        re.match(r'^\s*appellant.*', text, re.IGNORECASE) or \
        re.match(r'^\s*petitioner.*', text, re.IGNORECASE):
        next_block_label = "PETITIONER"
        current_block_end = True
    elif re.match(r'^\s*And *\:?\s*$', text) or re.match(r'^\s*AND *\:?\s*$', text) or\
            re.match(r'^\s*v\/?s[\:\s\.]*$', text,re.IGNORECASE) or \
            re.match(r'^\s*versus[\:\s\.]*$',text, re.IGNORECASE) or \
            re.match(r'^\s*respondent.*', text, re.IGNORECASE):
        next_block_label = "RESPONDENT"
        current_block_end = True
    elif re.match(r'.*\n *\n+ *$', text):
        current_block_end = True

    return current_block_end ,next_block_label


def get_label_for_unknown_ents(block_label, label_indicated_by_previous_block,block_in_sequence):
    ######## for the entities where keywords are not found in same sentence, try to see if block labels could be used
    if block_label is not None:
        label_for_unknown_ents = block_label
    elif block_label is None and label_indicated_by_previous_block is not None and block_in_sequence:
        label_for_unknown_ents = label_indicated_by_previous_block
    else:
        label_for_unknown_ents = None
    return label_for_unknown_ents

@Language.component("extract_preamble_entities")
def extract_preamble_entities(doc):
    keyword_dict = {
    'lawyer_keywords' : ['advocate','adv.','counsel','lawyer','adv','advocates','advs.','advs'],
    'judge_keywords' : ['justice','honourable',"hon'ble",'coram',"coram:","bench"],
    'petitioner_keywords' : ['appellant','petitioner','appellants','petitioners','petitioner(s)','petitioner(s','applicants','applicant','prosecution','complainant'],
    'respondent_keywords' : ['respondent','defendent','respondents'],
    'stopwords':['mr.','mrs.']}

    keywords = []
    for key,kw_list in keyword_dict.items():
        keywords.extend(kw_list)

    new_ents = []
    block_label = None
    next_block_label = None
    block_ents = []
    current_block_end =True
    block_start_with_sequence_number = False
    label_indicated_by_previous_block = None
    block_label_carry_forward_over_emptyblock_cnt = 0
    previous_block_sequence_number = 0
    sentences_cnt = len([i for i in doc.sents])
    block_in_sequence =False
    for sent_number, sent in enumerate(doc.sents):
        ###### check if new block is starting with serial number
        if current_block_end:
            if re.match(r'^\d[\.\)\]\s]+.*',sent.text):
                block_start_with_sequence_number = True
                block_start_number = int(re.search(r'^\d+',sent.text ).group())
                if block_start_number == previous_block_sequence_number+1:
                    block_in_sequence = True
                    previous_block_sequence_number += 1
                else:
                    block_in_sequence = False
                    previous_block_sequence_number = 0
                    block_label_carry_forward_over_emptyblock_cnt = 0


        ########## get the entity type by matching with keywords
        sent_label = match_span_with_keyword(sent, keyword_dict)

        ########## Use the first sentence label for the block label
        if sent_label is not None and block_label is None and sent_label not in ['COURT','JUDGE']:
            block_label = sent_label

        ########### get proper nouns from sentence which are candidates for entities
        sent_proper_nouns = extract_proper_nouns(sent, keywords)


        for chunk in sent_proper_nouns:
            if sent_label is not None:
                ######## add proper nouns to entities where keywords are present in same sentence.
                new_ent = {'start':chunk.start, 'end':chunk.end, 'label' : sent_label}
                block_ents.append(new_ent)
            else:
                ###### decide the entity of proper noun later based on block keywords
                new_ent = {'start': chunk.start, 'end': chunk.end, 'label': 'UNKNOWN'}
                block_ents.append(new_ent)

        ######### Identify end of block
        current_block_end,keyword_suggested_next_block_label = check_if_sentence_is_at_end_of_block(sent.text)

        ######## if current block is ending then choose entities to be added
        if current_block_end or sent_number == sentences_cnt-1:
            label_for_unknown_ents = get_label_for_unknown_ents(block_label,label_indicated_by_previous_block,block_in_sequence)
            sequence_number_suggested_next_block_label,block_label_carry_forward_over_emptyblock_cnt,previous_block_sequence_number = add_chunk_entities(new_ents,block_ents,label_for_unknown_ents,doc,block_start_with_sequence_number,label_indicated_by_previous_block,block_label_carry_forward_over_emptyblock_cnt,block_in_sequence,previous_block_sequence_number)
            next_block_label = get_next_block_label(keyword_suggested_next_block_label,sequence_number_suggested_next_block_label)

            block_ents= []
            block_start_with_sequence_number = False
            label_indicated_by_previous_block = next_block_label
            block_label = None


    doc.ents = new_ents
    return doc
