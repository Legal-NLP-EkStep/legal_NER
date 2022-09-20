# legal_NER
## 1. Why Seperate NER for Indian Court Judgments?
Named Entities Recognition is commonly studied problem in Natural Language Processing and many pre-trained models are publicly available. However legal documents have peculiar named entities like names of petitioner, respondent, court, statute, provision, precedents,  etc. These entity types are not recognized by standard Named Entity Recognizer like spacy. Hence there is a need to develop a Legal NER model. But ther are no publicly available annotated datasets for this task for Indian courts. Due to peculiarity of Indian legal processes and terminoligies used, it is important to develop seperate legal NER for Indian court judgment texts.

## 2. Which Legal Entities are covered?
Some entities are extracted from Preamble of the judgements and some from judgement text. Preamble of judgment contains formatted metadata like names of parties, judges, lawyers,date, court etc. The text following preamble till the end of the judgment is called as the "judgment".
Below is an example ![Example NER output](NER_example.png)

This code can extract following named entities from Indian Court judgments.
<center>
 
| Named Entity             | Extract From    | Description |
|:---------------:|:--------:| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| COURT          | Preamble      | Name of the court which has delivered the current judgement |
| COURT           | Judgement      | Name of any court mentioned |
| PETITIONER  | Preamble, Judgment   | Name of the petitioners / appellants /revisionist  from current case |
| RESPONDENT | Preamble, Judgment   | Name of the respondents / defendents /opposition from current case |
| JUDGE | Premable | Name of the judges from current case |
| JUDGE | Judgment | Name of the judges of the current as well as previous cases |
| LAWYER | Preamble | Name of the lawyers from both the parties |
| DATE | Judgment  | Any date mentioned in the judgment |
| ORG | Judgment  | Name of organizations mentioned in text apart from court. E.g. Banks, PSU, private companies, police stations, state govt etc. |
| GPE | Judgment | Geopolitical locations which include names of countries,states,cities, districts and villages | 
| STATUTE | Judgment | Name of the act or law mentioned in the judgement |
| PROVISION | Judgment | Sections, sub-sections, articles, orders, rules under a statute |
| PRECEDENT | Judgment | All the past court cases referred in the judgement as precedent. Precedent consists of party names + citation(optional) or case number (optional) |
| CASE\_NUMBER | Judgment | All the other case numbers mentioned in the judgment (apart from precedent) where party names and citation is not provided |
| WITNESS    | Judgment   | Name of witnesses in current judgment |
| OTHER_PERSON    | Judgment   | Name of the all the person that are not included in petitioner,respondent,judge and witness |     
 
</center>

More detailed definitions with examples can be found [here](https://docs.google.com/presentation/d/e/2PACX-1vSpWE_Qk9X_wBh7xJWPyYcWcME3ZBh_HmqeZOx58oMLyJSi0Tn0-JMWKI-HsQIRuUTbQHPql6MlU7OS/pub?start=false&loop=false&delayms=3000)
## 3. Data
Training data is available [here](https://storage.googleapis.com/indianlegalbert/OPEN_SOURCED_FILES/NER/NER_TRAIN.zip).

Judgements obtained via [representative sample genration method](https://github.com/Legal-NLP-EkStep/legal_NER/tree/main/representative_judgments_sample) during the time period from 1950 to 2017 was used to take sentences for annotation of training data. Judgements from 2017 to 2021 were used to select test data judgments. For preannotations, we used spacy pretrained model(en_core_web_trf) with custom rules to predict the legal named entities. This model was used to select sentences which are likely to contain the legal named entities. We also tried to reduce class imbalance across the entities by upsampling the rare entities. The preannotated sentences were annotated by the legal experts and data scientists at OpenNyAI. 

Since the entities present in the preamble and judgment are different, 2 seperate files are provided for training data. There are 9435 judgement sentences and 1560 preambles. 
Entity Counts in Judgment train data

|Entity   |Count|
|------------|----|
|OTHER_PERSON|2653|
|PROVISION   |2384|
|DATE        |1885|
|STATUTE     |1804|
|ORG         |1441|
|GPE         |1398|
|PRECEDENT   |1351|
|COURT       |1293|
|CASE_NUMBER |1040|
|WITNESS     |881 |
|JUDGE       |567 |
|PETITIONER  |464 |
|RESPONDENT  |324 |

Entity Counts in Preamble train data

|Entity   |Count|
|------------|----|
|COURT     |1074|
|PETITIONER|2604|
|RESPONDENT|3538|
|LAWYER    |3505|
|JUDGE     |1758|

## 4. Baseline Model
Baseline model was trained using [spacy-transformers](https://spacy.io/usage/training) with roberta-base. The trained model was tested on test data and following are the results.

The trained model can be installed using

```pip install https://storage.googleapis.com/indianlegalbert/OPEN_SOURCED_FILES/NER/python_wheel/en_legal_ner_trf-3.2.0-py3-none-any.whl```

Install spacy pretrained model 

```pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.2.0/en_core_web_sm-3.2.0-py3-none-any.whl```

Use pretrained model to find all the entities in a given judgement.

Entities can be extracted in two ways:

1.Passing the whole judgment : Whole judgment is passed through the model and entities are extracted.
It take less time to run but can miss entities as compared to 'sent' method. Use text_type='doc' for this method.

2.Passing sentence by sentence:Each sentence is individually passed through model and entities are extracted.
It takes more time to run but more accurate than passing the whole judgment. Use text_type='sent' for this method.



```python 
import spacy
from data_preparation import get_text_from_indiankanoon_url
from spacy import displacy
from legal_ner import extract_entities_from_judgment_text

legal_nlp=spacy.load('en_legal_ner_trf')
judgment_text = get_text_from_indiankanoon_url('https://indiankanoon.org/doc/542273/')

preamble_spiltting_nlp = spacy.load('en_core_web_sm')
text_type='doc'
combined_doc = extract_entities_from_judgment_text(judgment_text,legal_nlp,preamble_spiltting_nlp,text_type)

########### visualize the entities
extracted_ent_labels = list(set([i.label_ for i in combined_doc.ents]))
colors = {'COURT': "#bbabf2", 'PETITIONER': "#f570ea", "RESPONDENT": "#cdee81", 'JUDGE': "#fdd8a5",
          "LAWYER": "#f9d380", 'WITNESS': "violet", "STATUTE": "#faea99", "PROVISION": "yellow",
          'CASE_NUMBER': "#fbb1cf", "PRECEDENT": "#fad6d6", 'DATE': "#b1ecf7", 'OTHER_PERSON': "#b0f6a2",
          'ORG':'#a57db5','GPE':'#7fdbd4'}
options = {"ents": extracted_ent_labels, "colors": colors}


displacy.serve(combined_doc, style='ent',port=8080,options=options)
```

## 5. Evaluation
Evaluation portal will be made available soon.

## Acknowledgements
This work is part of [OpenNyAI](https://opennyai.org/) mission which is funded by [EkStep](https://ekstep.org/) and [Agami](https://agami.in/). 
