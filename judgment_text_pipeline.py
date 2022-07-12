import spacy
import re
from spacy.language import Language
from spacy.tokens import Span
from nltk.tag import pos_tag
from spacy import displacy
from dateparser import parse
from dateparser import parse
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
            ent = Span(doc, token_start, token_number + 1, label="POLICE STATION")

            new_ents.append(ent)
    return new_ents


def get_precedents(doc, text, starts):
    '''Uses regex to identify the precedents based on keyword 'vs',merges citations with precedents and returns precedent as a new entity'''
    new_ents = []
    final_ents = []
    regex_vs = r'\b(?i)((v(\.|/)*s*\.*)|versus)\s+'
    for match in re.finditer(regex_vs, text):

        token_number = starts.index(min(starts, key=lambda x: abs(match.span()[0] - x)))
        token_number_en=starts.index(min(starts, key=lambda x: abs(match.span()[1] - x)))

        token_number_start = token_number
        token_number_end = token_number_en-1

        i = token_number_start - 1
        j = token_number_end+1

        while i>-1 and (doc[i].text[0].isupper() or doc[i].text.startswith('other') or doc[i].text in ('of', '-', '&', '@', '(', ')', '\n', '.','and','another','anr','the',',','alias','/','[',']','by') or doc[i].text.isdigit()):

            token_number_start = i

            i = i - 1

        while j<len(doc) and (doc[j].text[0].isupper() or doc[j].text.startswith('other') or doc[j].text in ('of', '-', '&', '@', '(', ')', '\n', '.','and','another','anr','the','reported', 'in','alias','/','[',']','by') or doc[j].text.isdigit()):

            token_number_end = j


            if ',' in doc[j].text:
                break
            j = j + 1
        # import pdb;pdb.set_trace()
        if token_number_start > -1 and token_number_start<token_number:

            if token_number_end > token_number_start + 2 and token_number_end > token_number and token_number_end != token_number:
                ent = Span(doc, token_number_start, token_number_end + 1, label="PRECEDENT")

                final_ents.append(ent)

    citation_entities = get_citation(doc, text, starts)

    for ents in final_ents:
        token_num = ents.end
        if len(citation_entities) == 0:
            break
        citation_entity = (min(citation_entities, key=lambda x: abs(ents.end - x.start)))

        if (
                (  ( token_num == citation_entity.start or token_num > citation_entity.start) and token_num < citation_entity.end)    or (token_num+1==citation_entity.start and doc[token_num].text==',')):

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
        if start_char<end_char:

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
        if text in [ 'sub-section', 'sub-sections','subsection','sections','section', 's.', 'ss.', 's', 'ss', 'u/s', 'u/s.', 'u/ss', 'u/s.s']:

            spans_start = i

            count = i + 1
            if count>=len(doc):
                break

            next_token = doc[count]
            next_text = next_token.text.strip().lower()

            while (num_there(next_text) or next_text in ['to', 'and', ',', '/', '', '(', ')', '.','&']) and count<len(doc)-1 :
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


def get_entity(regex, doc, text, label):
    '''returns entity based on the given regex'''

    new_ents = []
    for match in re.finditer(regex, text):
        ent = doc.char_span(match.span()[0], match.span()[1], label=label, alignment_mode="expand")



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
    regex_statute = r'(?i)((i\.*\s*p\.*\s*c\.*\s*)|(c\.*\s*r\.*\s*p\.*\s*c\.*\s*)|(indian*\s*penal\s*code\s*)|(penal\s*code\.*\s*)|(code\s*of\s*criminal\s*procedure\s*)\n*)'

    regex_pw = r"\b(((?i)\s*\(*((P|D)\.*W\.*s*)+\-*\s*(\d*\s*\,*\)*(and|to)*)*)|(?i)witness\s*)"
    regex_app = r'(?i)\b(appellant|appellants|petitioner|petioners)\s*(((?i)no\.\s*\d+)|((?i)numbers)|((?i)number)|((?i)nos\.\s*\d+))*\s*(\d+|\,|and|to|\s*|–)+'
    regex_judge_bef = r'\b(?i)(J\.)$'
    regex_judge_aft=r'\b(?i)(justice|judge)'
    respondent_keywords = get_entity(regex_res, doc, text, 'key-rs')
    appellant_keywords = get_entity(regex_app, doc, text, 'key-ap')
    witness_keywords = get_entity(regex_pw, doc, text, 'key-pw')
    judge_keywords_bef = get_entity(regex_judge_bef, doc, text, 'key-jud-bef')
    judge_keywords_aft = get_entity(regex_judge_aft, doc, text, 'key-jud-aft')
    police_station = get_police_station(doc, text, starts)
    precedents = get_precedents(doc, text, starts)
    court_cases = get_court_case(doc, text, starts)
    statutes = get_entity(regex_statute, doc, text, 'STATUTE')
    provisions = get_provisions(doc)
    new_ents.extend(respondent_keywords)
    new_ents.extend(appellant_keywords)
    new_ents.extend(witness_keywords)
    new_ents.extend(judge_keywords_bef)
    new_ents.extend(judge_keywords_aft)
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

    elif ent_text.lower().find('article') > -1:
        section = ent_text.lower().find('article')
    else:
        section = -1
    if section != -1:
        if section < ent_text.find('of'):
            ents = doc.char_span(ent.start_char, ent.start_char + ent_text.find('of'), label="PROVISION",
                                 alignment_mode="expand")
            new_ents.append(ents)
            ents = doc.char_span(ent.start_char + ent_text.find('of') + 2, ent.end_char, label="STATUTE",
                                 alignment_mode="expand")
            new_ents.append(ents)
        else:
            ents = doc.char_span(ent.start_char + ent_text.find('of') + 2, ent.end_char, label="PROVISION",
                                 alignment_mode="expand")
            new_ents.append(ents)
            ents = doc.char_span(ent.start_char, ent.start_char + ent_text.find('of'), label="STATUTE",
                                 alignment_mode="expand")
            new_ents.append(ents)

    return new_ents


def get_provision_statute_from_law_using_keyword(doc, ent):
    '''Detects provision and statute from entity law identified by default NER' using keywords'''
    new_ents = []
    ent_text = ent.text
    if (ent_text.lower().find('act')!= -1  or ent_text.lower().find('code')  != -1 or 'constitution' in ent_text.lower()) and len(ent_text)>4:
        ent.label_ = 'STATUTE'
        new_ents.append(ent)
    elif ( ent_text.lower().find('section')!= -1 or  ent_text.lower().find('article') != -1) and len(ent_text)>7:
        ent.label_ = 'PROVISION'
        new_ents.append(ent)
    else:
        new_ents.append(ent)
    return new_ents


def get_prpopern_entitiy(doc, ent, entity_label):
    '''Detects the propernoun/person in the given string'''
    token_num = ent.end
    new_ents = []

    while len(doc) > token_num and (
            doc[token_num].ent_type_ == "PERSON" or doc[token_num].text.lower() in [',','dr.','mr.','mrs.','@'] or doc[token_num].pos_ == 'PROPN' ):
        token_num = token_num + 1
    if token_num > ent.end + 1:
        new_ent = Span(doc, ent.end, token_num, label=entity_label)
        new_ents.append(new_ent)
    return new_ents


def get_witness(doc, new_ent):
    '''Detects witness using the keyword key-pw'''
    new_ents = []
    delete=0
    token_num_end = new_ent.end
    token_num_start = new_ent.start - 1

    if token_num_end<len(doc) and doc[token_num_end].ent_type_ == "PERSON":


        while len(doc) > token_num_end and (
            doc[token_num_end].ent_type_ == "PERSON" or doc[token_num_end].text == ',' or doc[
        token_num_end].pos_ == 'PROPN'):
            token_num_end = token_num_end + 1
        if token_num_end > new_ent.end + 1:
            ent = Span(doc, new_ent.end, token_num_end, label="WITNESS")
            delete=1
            new_ents.append(ent)
    elif doc[token_num_start].ent_type_ == "PERSON":

        while  token_num_start>-1 and (doc[token_num_start].ent_type_ == "PERSON" or doc[token_num_start].text == ',' or doc[
        token_num_end].pos_ == 'PROPN'):
            token_num_start = token_num_start - 1




        if token_num_start < new_ent.start-1 and doc[token_num_start + 1].text != ',':

            ent = Span(doc, token_num_start + 1, new_ent.start, label="WITNESS")
            delete=-1

            new_ents.append(ent)


    return new_ents,delete


def get_prpopern_entitiy_before(doc, ent, entity_label):
    '''Detects the propernoun/person in the given string'''
    token_num = ent.start
    new_ents = []

    while (
            doc[token_num].ent_type_ == "PERSON" or doc[token_num].text == ',' or doc[token_num].pos_ == 'PROPN'):
        token_num = token_num - 1
    if token_num < ent.start - 1 and token_num>-1:
        new_ent = Span(doc, token_num + 1, ent.start, label=entity_label)
        new_ents.append(new_ent)
    return new_ents

def check_complete_nc(doc, new_ent,nc_list,label):
    new_ents = []


    if [new_ent.start,new_ent.end]  in nc_list:
        new_ents.append(new_ent)


    return new_ents

def check_dates(new_ents):
    entities=[]
    for ent in new_ents:
        if ent.label_=='DATE':

            if parse(ent.text, locales=['en-IN'], settings={'PARSERS': ['absolute-time'], 'STRICT_PARSING': True}):
                entities.append(ent)
        else:
            entities.append(ent)
    return entities



def check_org(doc,regex_courts,ents):
    new_ents=[]
    for ent in ents:
        if ent.label_!='ORG':
            new_ents.append(ent)
        else:

            if re.search(regex_courts,ent.text.lower()) is None :

                for tokens in range(ent.start,ent.end):
                    if ent.text.lower() in ['state','union']:
                        break

                    # if doc[tokens].pos_=='PROPN':

                    if pos_tag([ent.text.lower()])[0][1] =='NNP':
                        new_ents.append(ent)
                        break



    return new_ents

def check_statutes(doc,ents):
    new_ents=[]
    for ent in ents:
       if ent.label !='STATUTE':
           new_ents.append(ent)
       else:
            end_token = ent.end
            if end_token >= len(doc):
                new_ents.append(ent)
            else:
                match = re.match(r'.*(([1-3][0-9]{3})|,)', doc[end_token].text)
                token_num = end_token
                while match is not None:
                    token_num = token_num + 1
                    match = re.match(r'.*(([1-3][0-9]{3})|,)', doc[token_num].text)

                ent = Span(doc, ent.start, token_num, label='STATUTE')
                new_ents.append(ent)
    return new_ents


@Language.component("detect_post_entities")
def detect_post_entities(doc):
    regex_courts = r'\b(?i)((the)*\s*((high|trial|session|sessions|honourable|honble|hon\'ble)+\s*court*s*\s*)|(court\s*of\s*(session|sessions)+\s*)|(tribunal+\s*))$'
    '''Works on top of default NER to identify entities'''
    new_ents = []
    to_delete=[]
    nc_list = []
    for noun_chunk in doc.noun_chunks:
        nc_list.append([noun_chunk.start, noun_chunk.end])

    for index,new_ent in enumerate(list(doc.ents)):

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


            if any(re.findall(r'court|tribunal|magistrate|judge', ent_text, re.IGNORECASE)) and re.search(regex_courts,ent_text) is None :

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


        #
        # elif new_ent.label_ == "GPE":
        #     gpe = check_complete_nc(doc, new_ent,nc_list ,'GPE')
        #     new_ents.extend(gpe)
        elif new_ent.label_ == "key-rs":
            respondents = get_prpopern_entitiy(doc, new_ent, 'RESPONDENT')
            new_ents.extend(respondents)
        elif new_ent.label_ == "key-ap":
            appellants = get_prpopern_entitiy(doc, new_ent, 'PETITIONER')
            new_ents.extend(appellants)
        elif new_ent.label_ == "key-pw":
            witness,delete = get_witness(doc, new_ent)
            if delete!=0:

                to_delete.append(len(new_ents)+delete)

            new_ents.extend(witness)


        elif new_ent.label_ == "key-jud-bef":
            judge = get_prpopern_entitiy_before(doc, new_ent, 'JUDGE')
            new_ents.extend(judge)
        elif new_ent.label_ == "key-jud-aft":
            judge = get_prpopern_entitiy(doc, new_ent, 'JUDGE')
            new_ents.extend(judge)



        else:

            new_ents.append(new_ent)
    for ele in sorted(to_delete, reverse=True):
        del new_ents[ele]

    '''new_ents = [ent for ent in new_ents if
                ent.label_ not in ['LOC', 'PERSON', 'LAW', 'MONEY', 'CARDINAL','ORDINAL','FAC','WORK_OF_ART','QUANTITY',
                                   'PERCENT','TIME','PRODUCT','LANGUAGE','NORP','EVENT','FACTORY']]'''


    for ent in new_ents:
        if ent.label_=='PERSON':
            ent.label_='OTHER_PERSON'




    new_ents = filter_overlapping_entities(new_ents)
    new_ents=check_dates(new_ents)
    new_ents=check_org(doc,regex_courts,new_ents)
    new_ents=postprocess_entities(doc,new_ents)

    doc.ents = new_ents

    return doc

def postprocess_entities(doc,ents):
    postprocess_keywords=['dr.','mr.','mrs.','ms.','.',',','in','of','and','&','the']
    new_ents=[]
    for ent in ents:
        new_start=ent.start
        new_end=ent.end

        if doc[ent.start].text.lower() in postprocess_keywords:
            new_start=ent.start+1
        if doc[ent.end-1].text.lower() in postprocess_keywords:
            new_end=ent.end-1
        if new_end>new_start and (new_start!=ent.start or new_end !=ent.end):
            new_ents.append(Span(doc,new_start, new_end, label=ent.label_))
        else:
            new_ents.append(ent)
    return new_ents
def get_judgment_text_pipeline():
    '''Returns the xspacy pipeline for processing of the judgment text'''
    nlp_judgment = spacy.load("en_core_web_trf", disable=[])
    nlp_judgment.add_pipe("detect_pre_entities", before="ner")
    nlp_judgment.add_pipe("detect_post_entities", after="ner")
    return nlp_judgment


if __name__ == "__main__":
   text='''However, while this Commission was functioning, the Parliament constituted a Committee on welfare of Other Backward Classes under the Chairmanship of Shri B.K. Handique which presented its first report on 27 th August 2012 and it recommended that the NCBC should be conferred with a constitutional status and this saw light of the day by introduction of 123rd Bill.'''
   nlp=get_judgment_text_pipeline()
   doc=nlp(text)
   displacy.serve(doc, style='ent', port=8080)