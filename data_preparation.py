
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
import re
def convert_upper_case_to_title(txt):
    ########### convert the uppercase words to title case for catching names in NER
    title_tokens =  []
    for token in txt.split(' '):
        title_subtokens = []
        for subtoken in token.split('\n'):
            if subtoken.isupper():
                title_subtokens.append(subtoken.title())
            else:
                title_subtokens.append(subtoken)
        title_tokens.append('\n'.join(title_subtokens))
    title_txt = ' '.join(title_tokens)
    return title_txt

def guess_preamble_end(truncated_txt, nlp):
    ######### Guess the end of preamble using hueristics
    preamble_end = 0
    truncated_doc = nlp(truncated_txt)
    successive_preamble_pattern_breaks = 0
    preamble_patterns_breaks_theshold = 1 ####### end will be marked after these many consecutive sentences which dont match preamble pattern
    sent_list = [sent for sent in truncated_doc.sents]
    for sent_id,sent in enumerate(sent_list):
        ###### check if verb is present in the sentence
        verb_exclusions=['reserved','pronounced','dated','signed']
        sent_pos_tag = [token.pos_ for token in sent if token.lower_ not in verb_exclusions]
        verb_present = 'VERB' in sent_pos_tag

        ###### check if uppercase or title case
        allowed_lowercase = ['for','at','on','the','in','of']
        upppercase_or_titlecase = all([token.text in allowed_lowercase or token.is_upper or token.is_title or token.is_punct for token in sent if token.is_alpha])

        if verb_present and not upppercase_or_titlecase:
            successive_preamble_pattern_breaks+=1
            if successive_preamble_pattern_breaks>preamble_patterns_breaks_theshold:
                preamble_end = sent_list[sent_id-preamble_patterns_breaks_theshold-1].end_char
                break
        else:
            if successive_preamble_pattern_breaks>0 and (verb_present or not upppercase_or_titlecase):
                preamble_end = sent_list[sent_id - preamble_patterns_breaks_theshold - 1].end_char
                break
            else:
                successive_preamble_pattern_breaks = 0
    return preamble_end

def seperate_and_clean_preamble(txt,preamble_splitting_nlp):
    ########## seperate preamble from judgment text

    ######## get preamble end offset based on keywords
    keyword_preamble_end_offset = get_preamble_end_char_offset(txt,court='None')
    if keyword_preamble_end_offset==0:
        preamble_end_offset = 5000 ######## if keywords not found then set arbitrarty value
    else:
        preamble_end_offset = keyword_preamble_end_offset + 200 ######## take few more characters as judge names are written after JUDGEMENT keywords
    truncated_txt = txt[:preamble_end_offset]
    guessed_preamble_end = guess_preamble_end(truncated_txt, preamble_splitting_nlp)

    if guessed_preamble_end==0 :
        preamble_end = keyword_preamble_end_offset
    else:
        preamble_end = guessed_preamble_end

    preamble_txt = txt[:preamble_end]
    title_txt = convert_upper_case_to_title(preamble_txt)
    return title_txt,preamble_end


def get_text_from_indiankanoon_url(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req, timeout=10).read()
    page_soup = soup(webpage, "html.parser")
    judgment_txt = page_soup.text
    ########### Remove the text before start of main judgment
    judgement_start_pattern = 'Free for one month and pay only if you like it.'
    if judgment_txt.find(judgement_start_pattern) != -1:
        judgment_txt = judgment_txt.split(judgement_start_pattern,1)[1]
    judgment_txt = judgment_txt.strip().split('\n',2)[2] ##### remove first two lines which tell court name & case

    ########### Remove the extra information added by IndianKanoon if it  exists
    judgment_txt = re.sub(r'^Equivalent citations\:.*\n','',judgment_txt)
    judgment_txt = re.sub(r'^Author\:.*\n', '', judgment_txt)
    judgment_txt = re.sub(r'^Bench\:.*\n', '', judgment_txt)
    return judgment_txt.strip()

def get_preamble_end_char_offset(judgment_txt,court):
    ###### Find the end of preamble as per the court name
    if court == "SC_judgements_headnotes":
        split_dict = split_supreme_court_judgement_with_headnotes(judgment_txt)
        if split_dict.get('judgement') is None:
            preamble_end = 0
        else:
            if split_dict['judgement'] == "":
                preamble_end = 0
            else:
                judgement_keyword_start = judgment_txt.find('\nJUDGMENT:')
                if judgement_keyword_start==-1:
                    preamble_end = 0
                else:
                    preamble_end = judgement_keyword_start+10

    else:
        preamble_end = remove_unwanted_text(judgment_txt)

    return  preamble_end



def remove_unwanted_text(text):
    '''Looks for pattern  which typically starts the main text of jugement.
    The text before this pattern contains metadata like name of paries, judges and hence removed'''
    pos_list = []
    len = 0
    pos = 0
    pos_list.append(text.find("JUDGMENT & ORDER"))
    pos_list.append(text.find("J U D G M E N T"))
    pos_list.append(text.find("JUDGMENT"))
    pos_list.append(text.find("O R D E R"))
    pos_list.append(text.find("ORDER"))

    for i, p in enumerate(pos_list):

        if p != -1:
            if i == 0:
                len = 16
            elif i == 1:
                len = 15
            elif i == 2:
                len = 8
            elif i == 3:
                len = 9
            elif i == 4:
                len = 5
            pos = p + len
            break

    return pos

def split_supreme_court_judgement_with_headnotes(judgement_raw_text:str)->dict:
    ####### takes raw text as input and returns dictionary which has keys as "preamble","act","headnote","judgement" and
    # value as corrosponding text

    boundaries_list = [{'section':'preamble','start_index':0}]

    ###### add acts boundries if found
    act_keyword_start = judgement_raw_text.find('\nACT:')
    if act_keyword_start!= -1:
        act_text_start = act_keyword_start + 5
        boundaries_list.append({'section': 'act', 'keyword_start':act_keyword_start,'start_index': act_text_start})

    ###### add headnote boundries if found
    headnote_keyword_start = judgement_raw_text.find('\nHEADNOTE:')
    if headnote_keyword_start!= -1:
        headnote_text_start = headnote_keyword_start + 10
        boundaries_list.append({'section': 'headnote', 'keyword_start':headnote_keyword_start, 'start_index': headnote_text_start})

    ###### add judgement boundries if found
    judgement_keyword_start = judgement_raw_text.find('\nJUDGMENT:')
    if judgement_keyword_start!= -1:
        judgement_text_start = judgement_keyword_start + 11
        boundaries_list.append({'section': 'judgement', 'keyword_start':judgement_keyword_start, 'start_index': judgement_text_start})


    split_text_dict = {}
    for i,section in enumerate(boundaries_list):
        section_start = section['start_index']
        if i == len(boundaries_list)-1:
            section_end = len(judgement_raw_text)
        else:
            section_end = boundaries_list[i+1]['keyword_start'] - 1
        split_text_dict[section['section']] = judgement_raw_text[section_start:section_end]

    return split_text_dict
