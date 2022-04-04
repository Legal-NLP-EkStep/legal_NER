import spacy
import re
from spacy.language import Language
from spacy.tokens import Span

def get_citation(doc, text, starts):
    '''Uses regex to identify citations in the judgmment and returns citation as a new entity'''
    regex = '(\(\d+\)|\d+|\[\d+\])\s*(\(\d+\)|\d+|\[\d+\])*\s*[A-Z]+\s*(\(\d+\)|\d+|\[\d+\])+\s*(\(\d+\)|\d+|\[\d+\])*\s*'
    new_ents = []
    for match in re.finditer(regex, text):
        token_number_start = starts.index(min(starts, key=lambda x: abs(match.span()[0] - x)))
        token_number_end = starts.index(min(starts, key=lambda x: abs(match.span()[1] - x)))
        if '(' in doc[token_number_start:token_number_end].text and ')' in doc[
                                                                           token_number_start:token_number_end].text:
            ent = Span(doc, token_number_start, token_number_end, label="CITATION")
            new_ents.append(ent)

    return new_ents



def get_police_station(doc, text, starts):
    '''Uses regex to identify the police station and returns PoliceStation as a new entity'''
    new_ents = []
    regex_ps = r'(?i)\bp\.*s\.*\b'

    for match in re.finditer(regex_ps, text):
        token_number = starts.index(min(starts, key=lambda x: abs(match.span()[0] - x)))
        i = token_number - 1

        while doc[i].text[0].isupper():
            token_number_start = i
            i = i - 1
        token_start = i + 1
        if token_start != token_number:
            ent = Span(doc, token_start, token_number + 1, label="PoliceStation")

            new_ents.append(ent)
    return new_ents


def get_precedents(doc, text, starts):
    '''Uses regex to identify the precedents based on keyword 'vs',merges citations with precedents and returns precedent as a new entity'''
    new_ents = []
    final_ents = []
    regex_vs = r'(?i)\sv\.*s*\.*\b'
    for match in re.finditer(regex_vs, text):
        token_number = starts.index(min(starts, key=lambda x: abs(match.span()[0] - x)))
        token_number_start = token_number
        token_number_end = token_number

        i = token_number_start - 1
        j = token_number_end + 1

        while doc[i].text[0].isupper() or doc[i].text.startswith('other') or doc[i].text in (
                'of', '-', '&', '@', '(', ')', '\n', '.') or doc[i].text.isdigit():
            if ',' in doc[i].text:
                break
            token_number_start = i
            i = i - 1

        while doc[j].text[0].isupper() or doc[j].text.startswith('other') or doc[j].text in (
                'of', '-', '&', '@', '(', ')', '\n', 'others', '.') or doc[i].text.isdigit():
            token_number_end = j

            if ',' in doc[j].text:
                break
            j = j + 1

        if token_number_end > token_number_start + 2 and token_number_start != token_number and token_number_end != token_number:
            ent = Span(doc, token_number_start, token_number_end + 1, label="PRECEDENT")

            final_ents.append(ent)

    citation_entities = get_citation(doc, text, starts)

    for ents in final_ents:
        token_num = ents.end
        if len(citation_entities) == 0:
            break
        citation_entity = (min(citation_entities, key=lambda x: abs(ents.end - x.start)))

        if (token_num + 1 == citation_entity.start or  token_num > citation_entity.start )and token_num < citation_entity.end:

            citation_entities.remove(citation_entity)
            ent = Span(doc, ents.start, citation_entity.end, label="PRECEDENT")
            new_ents.append(ent)
        else:
            new_ents.append(ents)

    for citation_entity in citation_entities:
        ent = Span(doc, citation_entity.start, citation_entity.end, label="PRECEDENT")
        new_ents.append(ent)

    for ents in final_ents:
        new_ents.append(ents)
    return new_ents


def get_court_case(doc, text, starts):
    '''Uses regex to identify the case numbers  and returns CASE_NUMBER as a new entity'''
    new_ents = []
    regex_court_case = r'((?i)(no.)+(\s*|\n)[0-9]+\s*(/|of)\s*[0-9]+)'

    for match in re.finditer(regex_court_case, text):

        token_number = starts.index(min(starts, key=lambda x: abs(match.span()[0] - x)))
        i = token_number - 1
        while doc[i].text[0].isupper():
            token_number = i
            i = i - 1
        start_char = starts[token_number]
        end_char = match.span()[1]

        ent = doc.char_span(start_char, end_char, label="CASE_NUMBER", alignment_mode="expand")
        new_ents.append(ent)
    return new_ents




def get_provisions(doc):
    '''Uses regex to identify the provision based on keyword section and returns Provision as a new entity'''
    new_ents = []

    for i, token in enumerate(doc):

        text = token.text.lower().strip()
        spans_start = -1
        spans_end = -1
        if text in ['section', 'sub-section', 'sections', 's.', 'ss.', 's', 'ss', 'u/s', 'u/s.', 'u/ss', 'u/s.s']:

            spans_start = i

            count = i + 1
            next_token = doc[count]
            next_text = next_token.text.strip().lower()

            while num_there(next_text) or next_text in ['to', 'and', ',', '/', '', '(', ')', '.']:
                count = count + 1
                next_token = doc[count]
                next_text = next_token.text.strip().lower()
            i = count - 1
            spans_end = i

        if spans_start != -1:
            if num_there(doc[spans_start:spans_end + 1].text):
                ent = Span(doc, spans_start, spans_end + 1, label="PROVISION")

                new_ents.append(ent)
    return new_ents


def filter_overlapping_entities(ents):
    '''Removes the overlapping entities in the judgmnent text'''
    filtered_ents = []
    for span in spacy.util.filter_spans(ents):
        filtered_ents.append(span)
    return filtered_ents

def get_entity(regex,doc,text,label):
    '''returns entity based on the given regex'''
    new_ents = []
    for x in re.finditer(regex, text):
        ent = doc.char_span(x.span()[0], x.span()[1], label=label, alignment_mode="expand")

        new_ents.append(ent)

    return new_ents


@Language.component("detect_pre_entities")
def detect_pre_entities(doc):
    '''Detects entities before ner using keyword matching'''
    text = doc.text

    starts = [tok.idx for tok in doc]
    new_ents = []
    final_ents = []


    regex_res = r'(?i)\b(respondent|respondents)\s*(((?i)no\.\s*\d+)|((?i)numbers)|((?i)number)|((?i)nos\.\s*\d+))*\s*(\d+|\,|and|to|\s*|–)+'
    regex_statute = r'(?i)((i\.*\s*p\.*\s*c\.*\s*)|(c\.*\s*r\.*\s*p\.*\s*c\.*\s*)|(indian*\s*penal\s*code\s*)|(penal\s*code\.*\s*)\n*)'
    regex_pw = r"\b(((?i)\s*\(*(P\.*W\.*s*)+\-*\s*(\d*\s*\,*\)*(and|to)*)*)|(?i)witness\s*)"
    regex_app = r'(?i)\b(appellant|appellants)\s*(((?i)no\.\s*\d+)|((?i)numbers)|((?i)number)|((?i)nos\.\s*\d+))*\s*(\d+|\,|and|to|\s*|–)+'
    respondent_keywords = get_entity(regex_res,doc,text,'key-rs')
    appellant_keywords = get_entity(regex_app,doc,text,'key-ap')
    witness_keywords =get_entity(regex_pw,doc,text,'key-pw')
    police_station = get_police_station(doc, text, starts)
    precedents = get_precedents(doc, text, starts)
    court_cases = get_court_case(doc, text, starts)
    statutes = get_entity(regex_statute,doc,text,'key-pw')
    provisions = get_provisions(doc)
    new_ents.extend(respondent_keywords)
    new_ents.extend(appellant_keywords)
    new_ents.extend(witness_keywords)
    new_ents.extend(police_station)
    new_ents.extend(precedents)
    new_ents.extend(court_cases)
    new_ents.extend(statutes)
    new_ents.extend(provisions)

    new_ents = filter_overlapping_entities(new_ents)

    doc.ents = new_ents

    return doc


def num_there(s):
    '''checks if string contains a digit'''
    return any(i.isdigit() for i in s)


def get_provision_statute_from_law_using_of(doc, ent):
    '''Detects provision and statute from entity law identified by default NER by breaking on keyword 'of'''
    new_ents = []
    ent_text = ent.text
    if ent_text.lower().find('section') > -1:
        section = ent_text.lower().find('section')
    elif ent_text.lower().find('sub-section') > -1:
        section = ent_text.lower().find('sub-section')
    else:
        section = -1

    if section != -1:
        if section < ent_text.find('of'):
            ent = doc.char_span(ent.start_char, ent.start_char + ent_text.find('of'), label="PROVISION",
                                alignment_mode="expand")
            new_ents.append(ent)
            ent = doc.char_span(ent.start_char + ent_text.find('of') + 2, ent.end_char, label="STATUTE",
                                alignment_mode="expand")
            new_ents.append(ent)
        else:
            ent = doc.char_span(ent.start_char + ent_text.find('of') + 2, ent.end_char, label="PROVISION",
                                alignment_mode="expand")
            new_ents.append(ent)
            ent = doc.char_span(ent.start_char, ent.start_char + ent_text.find('of'), label="STATUTE",
                                alignment_mode="expand")
            new_ents.append(ent)
    return new_ents


def get_provision_statute_from_law_using_keyword(doc, ent):
    '''Detects provision and statute from entity law identified by default NER' using keywords'''
    new_ents = []
    ent_text = ent.text
    if ent_text.lower().find('act') != -1:
        ent.label_ = 'STATUTE'
        new_ents.append(ent)
    elif ent_text.lower().find('section') != -1:
        ent.label_ = 'PROVISION'
        new_ents.append(ent)
    else:
        new_ents.append(ent)
    return new_ents


def get_prpopern_entitiy(doc, ent, entity_label):
    '''Detects the propernoun/person in the given string'''
    token_num = ent.end
    new_ents = []

    while len(doc) > token_num and (doc[token_num].ent_type_ == "PERSON" or doc[token_num].text == ',' or doc[token_num].pos_ == 'PROPN'):
        token_num = token_num + 1
    if token_num > ent.end + 1:
        new_ent = Span(doc, ent.end, token_num, label=entity_label )
        new_ents.append(new_ent)
    return new_ents


def get_witness(doc, new_ent):
    '''Detects witness using the keyword key-pw'''
    new_ents = []
    token_num_end = new_ent.end
    token_num_start = new_ent.start - 1

    while len(doc) > token_num_end and (
            doc[token_num_end].ent_type_ == "PERSON" or doc[token_num_end].text == ',' or doc[
        token_num_end].pos_ == 'PROPN'):
        token_num_end = token_num_end + 1

    while doc[token_num_start].ent_type_ == "PERSON" or doc[token_num_start].text == ',' or doc[
        token_num_end].pos_ == 'PROPN':
        token_num_start = token_num_start - 1

    if token_num_end > new_ent.end + 1:
        ent = Span(doc, new_ent.end, token_num_end, label="WITNESS")
        new_ents.append(ent)

    if token_num_start < new_ent.start and doc[token_num_start + 1].text != ',':
        ent = Span(doc, token_num_start + 1, new_ent.start, label="WITNESS")

        new_ents.append(ent)
    return new_ents


@Language.component("detect_post_entities")
def detect_post_entities(doc):
    '''Works on top of default NER to identify entities'''
    new_ents = []

    for new_ent in list(doc.ents):

        ent_text = new_ent.text

        if new_ent.label_ == "LAW":

            if 'case no.' in ent_text.lower():
                new_ent.label_ = 'CASE_NUMBER'
                new_ents.append(new_ent)

            elif ent_text.find('of') != -1:
                provision_statute_entities = get_provision_statute_from_law_using_of(doc, new_ent)
                new_ents.extend(provision_statute_entities)
            else:
                provision_statute_entities = get_provision_statute_from_law_using_keyword(doc, new_ent)
                new_ents.extend(provision_statute_entities)
        elif new_ent.label_ == "ORG":
            if 'court' in ent_text.lower():
                if len(ent_text.split(' ')) > 1:
                    ent = doc.char_span(new_ent.start_char, new_ent.end_char, label="COURT", alignment_mode="expand")
                    new_ents.append(ent)

            elif 'police station' in ent_text.lower():
                token_num = new_ent.end
                while len(doc) > token_num and (doc[token_num].ent_type_ == "GPE" or doc[token_num].text == ','):
                    token_num = token_num + 1
                if token_num > new_ent.end:
                    ent = Span(doc, new_ent.start, token_num, label="POLICE STATION")
                    new_ents.append(ent)
            else:

                token_num = new_ent.end
                while len(doc) > token_num and (doc[token_num].ent_type_ == "GPE" or doc[token_num].text == ','):
                    token_num = token_num + 1

                ent = Span(doc, new_ent.start, token_num, label="ORG")
                new_ents.append(ent)


        elif new_ent.label_ == "key-rs":
            respondents = get_prpopern_entitiy(doc, new_ent, 'RESPONDENT')
            new_ents.extend(respondents)
        elif new_ent.label_ == "key-ap":
            appellants = get_prpopern_entitiy(doc, new_ent, 'APPELLANT')
            new_ents.extend(appellants)
        elif new_ent.label_ == "key-pw":
            witness = get_witness(doc, new_ent)
            new_ents.extend(witness)


        else:
            new_ents.append(new_ent)

    new_ents = [ent for ent in new_ents if
                ent.label_ not in ['GPE', 'PERSON', 'LAW', 'DATE', 'MONEY', 'CARDINAL','ORDINAL','FAC','WORK_OF_ART','QUANTITY','PERCENT','TIME','PRODUCT']]

    new_ents = filter_overlapping_entities(new_ents)

    doc.ents = new_ents

    return doc

def get_judgment_text_pipeline():
    '''Returns the spacy pipeline for processing of the judgment text'''
    nlp_judgment = spacy.load("en_core_web_trf", disable=[])
    nlp_judgment.add_pipe("detect_pre_entities", before="ner")
    nlp_judgment.add_pipe("detect_post_entities", after="ner")
    return nlp_judgment
