# KG Extractor Test Results

**Date:** 2025-10-19 20:22:03

**Model:** Qwen3-30B

**Test Type:** Unified Entity and Relationship Extraction (Single LLM Call)

---

## Test Configuration

- **Text length:** 22075 characters
- **Max tokens:** 131072 (very large for comprehensive extraction)
- **Temperature:** 0.6
- **Timeout:** 3600 seconds
- **Min confidence:** 0.45

---

## Test Text

```
[ ![geeksforgeeks](https://media.geeksforgeeks.org/gfg-gg-logo.svg) ](https://www.geeksforgeeks.org/)
  * 
  * Tutorials
  * Courses
  * Tracks
    * Languages
    * Interview Preparation
    * Data Science
    * Dev Skills
    * Tools
    * Maths
  * Switch to Dark Mode
▲
[ Open In App ](https://geeksforgeeksapp.page.link/?link=https://www.geeksforgeeks.org/perplexity-for-llm-evaluation/?type%3Darticle%26id%3D1368724&apn=free.programming.programming&isi=1641848816&ibi=org.geeksforgeeks.GeeksforGeeksDev&efr=1)
# Perplexity for LLM Evaluation
Last Updated :  23 Jul, 2025
Comments
Improve
Suggest changes
4 Likes
Like
Report
****Perplexity**** is a metric that measures the ****uncertainty**** of a model's predictions. Specifically, in language models, it quantifies how well the model predicts the next word in a sequence. When a model makes a prediction, it assigns probabilities to possible next words. 
Mathematically, perplexity is calculated as:
\text{Perplexity} = 2^{H(p)}
where H(p)is the ****entropy**** of the model's predictions. 
****Entropy**** measures the level of uncertainty in the model's output. Lower entropy means the model is more certain about its predictions and therefore, the perplexity is lower.
Perplexity indicates the level of confidence the model has in its prediction—lower perplexity suggests higher confidence and better performance in predicting the next word, while higher perplexity signals more uncertainty and less reliability. In simple terms, perplexity represents the number of potential options the model is considering when making its prediction.
## Why is Perplexity Important for LLM Evaluation?
Perplexity is an important metric because it helps us assess how well a [large language model (LLM)](https://www.geeksforgeeks.org/artificial-intelligence/large-language-model-llm/) is predicting the next token in a sequence. Here's why perplexity matters:
  1. ****Prediction Accuracy:**** Perplexity gives insight into the accuracy of a model’s predictions. A low perplexity means the model is good at predicting words and likely generates coherent and fluent text.
  2. ****Confidence of the Model:**** It tells us how confident the model is in its predictions. If the perplexity is high, the model is likely uncertain about the next word, which could lead to incoherent text.
  3. ****Evaluation of Language Models:**** Perplexity helps evaluate language models like GPT-3, where predicting the next word or token is a crucial task. By using perplexity, we can determine whether a model is suitable for text generation, machine translation or summarization tasks.
## How is Perplexity Calculated?
First, we need to compute the ****log probability**** of the model’s predictions for each word in the sequence. Here’s a simplified version of the process:
  1. ****Prediction of the Next Token:**** Language model predicts the probability of the next word based on the input text.
  2. ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the probability into a more useful measure.
  3. ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is computed.
  4. ****Exponentiation to Get Perplexity:**** Final step is to exponentiate the average log-likelihood to get the perplexity score.
Perplexity for a sequence of words can be computed as: 
\text{Perplexity} = \exp\left( -\frac{1}{N} \sum_{i=1}^{N} \log p(w_i | w_{i-1}, w_{i-2}, \dots, w_1) \right)
where, 
  * p(w_i \mid w_{i-1}, \dots, w_1) is the predicted probability of the i^{\text{th}} word.
  * N is the total number of words in the sequence.
This formula tells us how many words, on average, the model is choosing from when predicting the next word. A lower perplexity indicates fewer choices, meaning the model is more confident.
## ****Calculating Perplexity for LLM Evaluation in Python****
### Step 1: Import Required Libraries
The first step is to import the necessary libraries. We need the torch library for handling tensor computations. 
Python `
```
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
```
`
```
import torch
```
```
from transformers import AutoTokenizer, AutoModelForCausalLM
```
### Step 2: Load Pre-Trained GPT-2 Model and Tokenizer
In this step, we load the pre-trained GPT-2 model and tokenizer. 
  * ****AutoTokenizer.from_pretrained(model_name):**** Loads the tokenizer for a pre-trained model.
  * ****AutoModelForCausalLM.from_pretrained(model_name):**** Loads the language model for causal language modeling (GPT-2 in this case).
  * ****tokenizer.pad_token = tokenizer.eos_token:**** Sets the end-of-sequence token (EOS) as the padding token, ensuring the model processes padding correctly.
Python `
```
# Load pre-trained GPT-2 model and tokenizer
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
# Assign the EOS token as the padding token
tokenizer.pad_token = tokenizer.eos_token
```
`
```
# Load pre-trained GPT-2 model and tokenizer
```
```
model_name = "gpt2"
```
```
tokenizer = AutoTokenizer.from_pretrained(model_name)
```
```
model = AutoModelForCausalLM.from_pretrained(model_name)
```
```
​
```
```
# Assign the EOS token as the padding token
```
```
tokenizer.pad_token = tokenizer.eos_token
```
### Step 3: Define the Perplexity Calculation Function
This function computes perplexity for a batch of input texts. 
Python `
```
def compute_perplexity_for_batch(input_texts):
    inputs = tokenizer(
        input_texts, return_tensors="pt", padding=True, truncation=True
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
    shift_logits = logits[:, :-1, :] 
    shift_labels = input_ids[:, 1:] 
    log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)
    target_log_probs = log_probs.gather(dim=-1, index=shift_labels.unsqueeze(-1)).squeeze(-1)
    target_log_probs = target_log_probs * attention_mask[:, 1:].to(log_probs.dtype)
    negative_log_likelihood = -target_log_probs.sum(dim=-1) / attention_mask[:, 1:].sum(dim=-1)
    perplexities = torch.exp(negative_log_likelihood)
    mean_perplexity_score = torch.mean(perplexities)
    return {
        "perplexities": perplexities.tolist(),
        "mean_perplexity": mean_perplexity_score.item()
    }
```
`
```
def compute_perplexity_for_batch(input_texts):
```
```
    inputs = tokenizer(
```
```
        input_texts, return_tensors="pt", padding=True, truncation=True
```
```
    )
```
```
​
```
```
    input_ids = inputs["input_ids"]
```
```
    attention_mask = inputs["attention_mask"]
```
```
​
```
```
    with torch.no_grad():
```
```
        outputs = model(input_ids, attention_mask=attention_mask)
```
```
        logits = outputs.logits
```
```
​
```
```
    shift_logits = logits[:, :-1, :] 
```
```
    shift_labels = input_ids[:, 1:] 
```
```
​
```
```
    log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)
```
```
    target_log_probs = log_probs.gather(dim=-1, index=shift_labels.unsqueeze(-1)).squeeze(-1)
```
```
    target_log_probs = target_log_probs * attention_mask[:, 1:].to(log_probs.dtype)
```
```
    negative_log_likelihood = -target_log_probs.sum(dim=-1) / attention_mask[:, 1:].sum(dim=-1)
```
```
    perplexities = torch.exp(negative_log_likelihood)
```
```
    mean_perplexity_score = torch.mean(perplexities)
```
```
​
```
```
    return {
```
```
        "perplexities": perplexities.tolist(),
```
```
        "mean_perplexity": mean_perplexity_score.item()
```
```
    }
```
### Step 4: Running the Example
Finally, we run the ****compute_perplexity_for_batch()**** function on a batch of input texts to compute and print the perplexity scores.
Python `
```
example_texts = [
    "Once upon a time, there was a brave knight.",
    "In a galaxy far, far away, a new adventure began."
]
# Compute perplexity scores for the batch of input texts
results = compute_perplexity_for_batch(example_texts)
print(f"Perplexity scores for each text: {results['perplexities']}")
print(f"Mean perplexity score: {results['mean_perplexity']}")
```
`
```
example_texts = [
```
```
    "Once upon a time, there was a brave knight.",
```
```
    "In a galaxy far, far away, a new adventure began."
```
```
]
```
```
​
```
```
# Compute perplexity scores for the batch of input texts
```
```
results = compute_perplexity_for_batch(example_texts)
```
```
print(f"Perplexity scores for each text: {results['perplexities']}")
```
```
print(f"Mean perplexity score: {results['mean_perplexity']}")
```
****Output:****
> Perplexity scores for each text: [25.61, 18.61]  
> Mean perplexity score: 22.11
#### ****Interpreting the Results:****
  1. ****Perplexity Score for Text 1**** : Perplexity for the sentence "Once upon a time, there was a brave knight." is ****25.61**** , indicating that the model had moderate uncertainty in predicting the next word.
  2. ****Perplexity Score for Text 2**** : Sentence "In a galaxy far, far away, a new adventure began." has a lower perplexity score of ****18.61**** , suggesting the model was more confident about predicting the next word.
  3. ****Mean Perplexity Score**** : Mean perplexity score for the batch of texts is ****22.11**** , which gives an overall sense of how well the model performed on these two sentences.
## Advantages of Perplexity 
Perplexity offers several advantages, making it a widely-used metric for evaluating language models. Let's explore its key benefits:
  1. ****Intuitive Measure:**** Perplexity provides an easy-to-understand measure of model performance. It translates the model’s uncertainty into a human-readable form, telling us how many choices the model is considering for the next word.
  2. ****Real-Time Evaluation**** : Perplexity is calculated quickly and can be used during model training to instantly assess how well the model is performing.
  3. ****Useful for Fine-Tuning**** : Checking perplexity during fine-tuning helps developers see if the model is getting better at making confident predictions.
## Limitations of Perplexity
Despite its advantages, perplexity has its limitations. While it’s an important metric, it doesn’t tell the full story. Let’s move into some of its challenges:
  1. ****Does Not Measure Understanding:**** A model with low perplexity may still produce incoherent or irrelevant text. Perplexity doesn't measure a model's ****understanding**** of the content, only its ability to predict the next word.
  2. ****Does Not Capture Long-Term Dependencies:**** Perplexity is based on immediate word predictions and may not capture longer-term dependencies or coherence across long sequences of text.
  3. ****Sensitive to Tokenization:**** A model tokenizes words can affect its perplexity score. For example, character-level models might have lower perplexity than word-level models, but that doesn't necessarily mean they are better at generating coherent text.
## Using Perplexity Alongside Other Metrics
Perplexity is an essential evaluation metric for large language models (LLMs), but it is not enough to rely solely on perplexity when assessing a model’s performance. To get a more comprehensive view of how well a model is performing, it's crucial to use ****perplexity**** in combination with other metrics:
  1. ****BLEU, ROUGE, and METEOR**** : These metrics compare generated text against reference texts and are widely used in tasks like machine translation and summarization.
  2. ****Human Evaluation**** : Human judges assess the quality of generated text based on fluency, relevance, and coherence. While subjective, this approach provides insights into aspects that automated metrics cannot capture.
  3. ****Factual Accuracy**** : Tools like knowledge-based QA systems or fact-checking frameworks evaluate whether the model's outputs are factually correct.
  4. ****Diversity and Creativity**** : Metrics such as repetition rate, novelty score, and entropy assess the diversity of generated text.
  5. ****Bias and Fairness**** : Evaluating models for harmful biases and fairness ensures their safe deployment in real-world applications.
By combining ****perplexity**** with these additional metrics, we can better evaluate a model’s ****predictive accuracy**** , ****fluency**** and ****real-world usability****. This combination allows us to detect models that not only predict correctly but also do so with confidence and coherence.
## Real-World Applications of Perplexity
Let’s look at some practical scenarios where perplexity is widely used in the evaluation of language models:
  1. ****Text Generation**** : For generating coherent and fluent text, perplexity helps ensure the model's predictions are confident and make sense.
  2. ****Machine Translation**** : Perplexity can be used to assess how well a translation model predicts the next word in the target language, which is crucial for high-quality translations.
  3. ****Chatbots and Virtual Assistants**** : In conversational AI, a low perplexity ensures that responses are fluent and contextually appropriate, improving user experience.
  4. ****Summarization Models**** : In text summarization, perplexity helps evaluate how well the model predicts the next word in a summary, ensuring readability and coherence.
By incorporating perplexity into your evaluation pipeline, you can gain deeper insights into your model's predictive confidence, guiding further improvements and making your AI applications more reliable and efficient.
[ A ](https://www.geeksforgeeks.org/user/anshvar235p/)
[anshvar235p](https://www.geeksforgeeks.org/user/anshvar235p/)
Follow
4
Improve
[ A ](https://www.geeksforgeeks.org/user/anshvar235p/)
[anshvar235p](https://www.geeksforgeeks.org/user/anshvar235p/)
Follow
4
Improve
Article Tags : 
### Explore
[Natural Language Processing (NLP) Tutorial 5 min read ](https://www.geeksforgeeks.org/nlp/natural-language-processing-nlp-tutorial/)
## Introduction to NLP
[Natural Language Processing (NLP) - Overview 9 min read ](https://www.geeksforgeeks.org/nlp/natural-language-processing-overview/)[NLP vs NLU vs NLG 3 min read ](https://www.geeksforgeeks.org/nlp/nlp-vs-nlu-vs-nlg/)[Applications of NLP 6 min read ](https://www.geeksforgeeks.org/nlp/applications-of-nlp/)[Why is NLP important? 6 min read ](https://www.geeksforgeeks.org/nlp/why-is-nlp-important/)[Phases of Natural Language Processing (NLP) 7 min read ](https://www.geeksforgeeks.org/machine-learning/phases-of-natural-language-processing-nlp/)[The Future of Natural Language Processing: Trends and Innovations 7 min read ](https://www.geeksforgeeks.org/blogs/the-future-of-natural-language-processing-trends-and-innovations/)
## Libraries for NLP
[NLTK - NLP 5 min read ](https://www.geeksforgeeks.org/python/NLTK-NLP/)[Tokenization Using Spacy 4 min read ](https://www.geeksforgeeks.org/nlp/tokenization-using-spacy-library/)[Python | Tokenize text using TextBlob 3 min read ](https://www.geeksforgeeks.org/machine-learning/python-tokenize-text-using-textblob/)[Introduction to Hugging Face Transformers 5 min read ](https://www.geeksforgeeks.org/artificial-intelligence/Introduction-to-hugging-face-transformers/)[NLP Gensim Tutorial - Complete Guide For Beginners 13 min read ](https://www.geeksforgeeks.org/nlp/nlp-gensim-tutorial-complete-guide-for-beginners/)[NLP Libraries in Python 9 min read ](https://www.geeksforgeeks.org/nlp/nlp-libraries-in-python/)
## Text Normalization in NLP
[Normalizing Textual Data with Python 7 min read ](https://www.geeksforgeeks.org/python/normalizing-textual-data-with-python/)[Regex Tutorial - How to write Regular Expressions? 6 min read ](https://www.geeksforgeeks.org/dsa/write-regular-expressions/)[Tokenization in NLP 8 min read ](https://www.geeksforgeeks.org/nlp/nlp-how-tokenizing-text-sentence-words-works/)[Lemmatization with NLTK 6 min read ](https://www.geeksforgeeks.org/python/python-lemmatization-with-nltk/)[Introduction to Stemming 6 min read ](https://www.geeksforgeeks.org/machine-learning/introduction-to-stemming/)[Removing stop words with NLTK in Python 6 min read ](https://www.geeksforgeeks.org/nlp/removing-stop-words-nltk-python/)[POS(Parts-Of-Speech) Tagging in NLP 6 min read ](https://www.geeksforgeeks.org/nlp/nlp-part-of-speech-default-tagging/)
## Text Representation and Embedding Techniques
[One-Hot Encoding in NLP 9 min read ](https://www.geeksforgeeks.org/nlp/one-hot-encoding-in-nlp/)[Bag of words (BoW) model in NLP 7 min read ](https://www.geeksforgeeks.org/nlp/bag-of-words-bow-model-in-nlp/)[Understanding TF-IDF (Term Frequency-Inverse Document Frequency) 4 min read ](https://www.geeksforgeeks.org/machine-learning/understanding-tf-idf-term-frequency-inverse-document-frequency/)[N-Gram Language Modelling with NLTK 3 min read ](https://www.geeksforgeeks.org/nlp/n-gram-language-modelling-with-nltk/)[Word Embedding using Word2Vec 5 min read ](https://www.geeksforgeeks.org/python/python-word-embedding-using-word2vec/)[Glove Word Embedding in NLP 8 min read ](https://www.geeksforgeeks.org/nlp/Glove-Word-Embedding-in-NLP/)[Overview of Word Embedding using Embeddings from Language Models (ELMo) 4 min read ](https://www.geeksforgeeks.org/python/overview-of-word-embedding-using-embeddings-from-language-models-elmo/)
## NLP Deep Learning Techniques
[NLP with Deep Learning 3 min read ](https://www.geeksforgeeks.org/nlp/nlp-with-deep-learning/)[Introduction to Recurrent Neural Networks 10 min read ](https://www.geeksforgeeks.org/machine-learning/introduction-to-recurrent-neural-network/)[What is LSTM - Long Short Term Memory? 5 min read ](https://www.geeksforgeeks.org/deep-learning/deep-learning-introduction-to-long-short-term-memory/)[Gated Recurrent Unit Networks 6 min read ](https://www.geeksforgeeks.org/machine-learning/gated-recurrent-unit-networks/)[Transformers in Machine Learning 4 min read ](https://www.geeksforgeeks.org/machine-learning/getting-started-with-transformers/)[seq2seq Model 6 min read ](https://www.geeksforgeeks.org/machine-learning/seq2seq-model-in-machine-learning/)[Top 5 PreTrained Models in Natural Language Processing (NLP) 7 min read ](https://www.geeksforgeeks.org/nlp/top-5-pre-trained-models-in-natural-language-processing-nlp/)
## NLP Projects and Practice
[Sentiment Analysis with an Recurrent Neural Networks (RNN) 5 min read ](https://www.geeksforgeeks.org/python/sentiment-analysis-with-an-recurrent-neural-networks-rnn/)[Text Generation using Recurrent Long Short Term Memory Network 4 min read ](https://www.geeksforgeeks.org/machine-learning/text-generation-using-recurrent-long-short-term-memory-network/)[Machine Translation with Transformer in Python 6 min read ](https://www.geeksforgeeks.org/nlp/machine-translation-with-transformer-in-python/)[Building a Rule-Based Chatbot with Natural Language Processing 4 min read ](https://www.geeksforgeeks.org/nlp/building-a-rule-based-chatbot-with-natural-language-processing/)[Text Classification using scikit-learn in NLP 5 min read ](https://www.geeksforgeeks.org/nlp/text-classification-using-scikit-learn-in-nlp/)[Text Summarization using HuggingFace Model 4 min read ](https://www.geeksforgeeks.org/nlp/text-summarizations-using-huggingface-model/)[Natural Language Processing Interview Question 15+ min read ](https://www.geeksforgeeks.org/nlp/advanced-natural-language-processing-interview-question/)
Like
[ ![geeksforgeeks-footer-logo](https://media.geeksforgeeks.org/auth-dashboard-uploads/gfgFooterLogo.png) ](https://www.geeksforgeeks.org/)
Corporate & Communications Address:
A-143, 7th Floor, Sovereign Corporate Tower, Sector- 136, Noida, Uttar Pradesh (201305) 
Registered Address:
K 061, Tower K, Gulshan Vivante Apartment, Sector 137, Noida, Gautam Buddh Nagar, Uttar Pradesh, 201305 
[![GFG App on Play Store](https://media.geeksforgeeks.org/auth-dashboard-uploads/googleplay.png)](https://geeksforgeeksapp.page.link/gfg-app) [![GFG App on App Store](https://media.geeksforgeeks.org/auth-dashboard-uploads/appstore.png)](https://geeksforgeeksapp.page.link/gfg-app)
  * Company
  * Explore
  * Tutorials
  * Courses
  * Videos
  * Preparation Corner
![Lightbox](https://www.geeksforgeeks.org/nlp/perplexity-for-llm-evaluation/)
Improvement
Suggest changes
Suggest Changes
Help us improve. Share your suggestions to enhance the article. Contribute your expertise and make a difference in the GeeksforGeeks portal.
![geeksforgeeks-suggest-icon](https://media.geeksforgeeks.org/auth-dashboard-uploads/suggestChangeIcon.png)
Create Improvement
Enhance the article with your expertise. Contribute to the GeeksforGeeks community and help create better learning resources for all.
![geeksforgeeks-improvement-icon](https://media.geeksforgeeks.org/auth-dashboard-uploads/createImprovementIcon.png)
Suggest Changes
min 4 words, max Words Limit:1000
## Thank You!
Your suggestions are valuable to us.
[](https://www.geeksforgeeks.org/nlp/perplexity-for-llm-evaluation/)
## What kind of Experience do you want to share?
[ Interview Experiences ](https://write.geeksforgeeks.org/posts-new?cid=e8fc46fe-75e7-4a4b-be3c-0c862d655ed0) [ Admission Experiences ](https://write.geeksforgeeks.org/posts-new?cid=82536bdb-84e6-4661-87c3-e77c3ac04ede) [ Career Journeys ](https://write.geeksforgeeks.org/posts-new?cid=5219b0b2-7671-40a0-9bda-503e28a61c31) [ Work Experiences ](https://write.geeksforgeeks.org/posts-new?cid=22ae3354-15b6-4dd4-a5b4-5c7a105b8a8f) [ Campus Experiences ](https://write.geeksforgeeks.org/posts-new?cid=c5e1ac90-9490-440a-a5fa-6180c87ab8ae) [ Competitive Exam Experiences ](https://write.geeksforgeeks.org/posts-new?cid=5ebb8fe9-b980-4891-af07-f2d62a9735f2)
Login Modal | GeeksforGeeks
New user ?Register Now
Continue with Google
or
Username or Email 
Password
Remember me
Forgot Password
# Create Account
Continue with Google
or
Username or Email
Password
Institution / Organization
Sign Up
*Please enter your email address or userHandle.
Back to Login
Reset Password

```

---

## Prompt Sent to LLM

```
You are an expert at extracting knowledge graphs from technical documentation.

Your task is to extract BOTH entities and relationships from the text below.

[[[
**Text:**
[ ![geeksforgeeks](https://media.geeksforgeeks.org/gfg-gg-logo.svg) ](https://www.geeksforgeeks.org/)
  * 
  * Tutorials
  * Courses
  * Tracks
    * Languages
    * Interview Preparation
    * Data Science
    * Dev Skills
    * Tools
    * Maths
  * Switch to Dark Mode
▲
[ Open In App ](https://geeksforgeeksapp.page.link/?link=https://www.geeksforgeeks.org/perplexity-for-llm-evaluation/?type%3Darticle%26id%3D1368724&apn=free.programming.programming&isi=1641848816&ibi=org.geeksforgeeks.GeeksforGeeksDev&efr=1)
# Perplexity for LLM Evaluation
Last Updated :  23 Jul, 2025
Comments
Improve
Suggest changes
4 Likes
Like
Report
****Perplexity**** is a metric that measures the ****uncertainty**** of a model's predictions. Specifically, in language models, it quantifies how well the model predicts the next word in a sequence. When a model makes a prediction, it assigns probabilities to possible next words. 
Mathematically, perplexity is calculated as:
\text{Perplexity} = 2^{H(p)}
where H(p)is the ****entropy**** of the model's predictions. 
****Entropy**** measures the level of uncertainty in the model's output. Lower entropy means the model is more certain about its predictions and therefore, the perplexity is lower.
Perplexity indicates the level of confidence the model has in its prediction—lower perplexity suggests higher confidence and better performance in predicting the next word, while higher perplexity signals more uncertainty and less reliability. In simple terms, perplexity represents the number of potential options the model is considering when making its prediction.
## Why is Perplexity Important for LLM Evaluation?
Perplexity is an important metric because it helps us assess how well a [large language model (LLM)](https://www.geeksforgeeks.org/artificial-intelligence/large-language-model-llm/) is predicting the next token in a sequence. Here's why perplexity matters:
  1. ****Prediction Accuracy:**** Perplexity gives insight into the accuracy of a model’s predictions. A low perplexity means the model is good at predicting words and likely generates coherent and fluent text.
  2. ****Confidence of the Model:**** It tells us how confident the model is in its predictions. If the perplexity is high, the model is likely uncertain about the next word, which could lead to incoherent text.
  3. ****Evaluation of Language Models:**** Perplexity helps evaluate language models like GPT-3, where predicting the next word or token is a crucial task. By using perplexity, we can determine whether a model is suitable for text generation, machine translation or summarization tasks.
## How is Perplexity Calculated?
First, we need to compute the ****log probability**** of the model’s predictions for each word in the sequence. Here’s a simplified version of the process:
  1. ****Prediction of the Next Token:**** Language model predicts the probability of the next word based on the input text.
  2. ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the probability into a more useful measure.
  3. ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is computed.
  4. ****Exponentiation to Get Perplexity:**** Final step is to exponentiate the average log-likelihood to get the perplexity score.
Perplexity for a sequence of words can be computed as: 
\text{Perplexity} = \exp\left( -\frac{1}{N} \sum_{i=1}^{N} \log p(w_i | w_{i-1}, w_{i-2}, \dots, w_1) \right)
where, 
  * p(w_i \mid w_{i-1}, \dots, w_1) is the predicted probability of the i^{\text{th}} word.
  * N is the total number of words in the sequence.
This formula tells us how many words, on average, the model is choosing from when predicting the next word. A lower perplexity indicates fewer choices, meaning the model is more confident.
## ****Calculating Perplexity for LLM Evaluation in Python****
### Step 1: Import Required Libraries
The first step is to import the necessary libraries. We need the torch library for handling tensor computations. 
Python `
```
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
```
`
```
import torch
```
```
from transformers import AutoTokenizer, AutoModelForCausalLM
```
### Step 2: Load Pre-Trained GPT-2 Model and Tokenizer
In this step, we load the pre-trained GPT-2 model and tokenizer. 
  * ****AutoTokenizer.from_pretrained(model_name):**** Loads the tokenizer for a pre-trained model.
  * ****AutoModelForCausalLM.from_pretrained(model_name):**** Loads the language model for causal language modeling (GPT-2 in this case).
  * ****tokenizer.pad_token = tokenizer.eos_token:**** Sets the end-of-sequence token (EOS) as the padding token, ensuring the model processes padding correctly.
Python `
```
# Load pre-trained GPT-2 model and tokenizer
model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
# Assign the EOS token as the padding token
tokenizer.pad_token = tokenizer.eos_token
```
`
```
# Load pre-trained GPT-2 model and tokenizer
```
```
model_name = "gpt2"
```
```
tokenizer = AutoTokenizer.from_pretrained(model_name)
```
```
model = AutoModelForCausalLM.from_pretrained(model_name)
```
```
​
```
```
# Assign the EOS token as the padding token
```
```
tokenizer.pad_token = tokenizer.eos_token
```
### Step 3: Define the Perplexity Calculation Function
This function computes perplexity for a batch of input texts. 
Python `
```
def compute_perplexity_for_batch(input_texts):
    inputs = tokenizer(
        input_texts, return_tensors="pt", padding=True, truncation=True
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
    shift_logits = logits[:, :-1, :] 
    shift_labels = input_ids[:, 1:] 
    log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)
    target_log_probs = log_probs.gather(dim=-1, index=shift_labels.unsqueeze(-1)).squeeze(-1)
    target_log_probs = target_log_probs * attention_mask[:, 1:].to(log_probs.dtype)
    negative_log_likelihood = -target_log_probs.sum(dim=-1) / attention_mask[:, 1:].sum(dim=-1)
    perplexities = torch.exp(negative_log_likelihood)
    mean_perplexity_score = torch.mean(perplexities)
    return {
        "perplexities": perplexities.tolist(),
        "mean_perplexity": mean_perplexity_score.item()
    }
```
`
```
def compute_perplexity_for_batch(input_texts):
```
```
    inputs = tokenizer(
```
```
        input_texts, return_tensors="pt", padding=True, truncation=True
```
```
    )
```
```
​
```
```
    input_ids = inputs["input_ids"]
```
```
    attention_mask = inputs["attention_mask"]
```
```
​
```
```
    with torch.no_grad():
```
```
        outputs = model(input_ids, attention_mask=attention_mask)
```
```
        logits = outputs.logits
```
```
​
```
```
    shift_logits = logits[:, :-1, :] 
```
```
    shift_labels = input_ids[:, 1:] 
```
```
​
```
```
    log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)
```
```
    target_log_probs = log_probs.gather(dim=-1, index=shift_labels.unsqueeze(-1)).squeeze(-1)
```
```
    target_log_probs = target_log_probs * attention_mask[:, 1:].to(log_probs.dtype)
```
```
    negative_log_likelihood = -target_log_probs.sum(dim=-1) / attention_mask[:, 1:].sum(dim=-1)
```
```
    perplexities = torch.exp(negative_log_likelihood)
```
```
    mean_perplexity_score = torch.mean(perplexities)
```
```
​
```
```
    return {
```
```
        "perplexities": perplexities.tolist(),
```
```
        "mean_perplexity": mean_perplexity_score.item()
```
```
    }
```
### Step 4: Running the Example
Finally, we run the ****compute_perplexity_for_batch()**** function on a batch of input texts to compute and print the perplexity scores.
Python `
```
example_texts = [
    "Once upon a time, there was a brave knight.",
    "In a galaxy far, far away, a new adventure began."
]
# Compute perplexity scores for the batch of input texts
results = compute_perplexity_for_batch(example_texts)
print(f"Perplexity scores for each text: {results['perplexities']}")
print(f"Mean perplexity score: {results['mean_perplexity']}")
```
`
```
example_texts = [
```
```
    "Once upon a time, there was a brave knight.",
```
```
    "In a galaxy far, far away, a new adventure began."
```
```
]
```
```
​
```
```
# Compute perplexity scores for the batch of input texts
```
```
results = compute_perplexity_for_batch(example_texts)
```
```
print(f"Perplexity scores for each text: {results['perplexities']}")
```
```
print(f"Mean perplexity score: {results['mean_perplexity']}")
```
****Output:****
> Perplexity scores for each text: [25.61, 18.61]  
> Mean perplexity score: 22.11
#### ****Interpreting the Results:****
  1. ****Perplexity Score for Text 1**** : Perplexity for the sentence "Once upon a time, there was a brave knight." is ****25.61**** , indicating that the model had moderate uncertainty in predicting the next word.
  2. ****Perplexity Score for Text 2**** : Sentence "In a galaxy far, far away, a new adventure began." has a lower perplexity score of ****18.61**** , suggesting the model was more confident about predicting the next word.
  3. ****Mean Perplexity Score**** : Mean perplexity score for the batch of texts is ****22.11**** , which gives an overall sense of how well the model performed on these two sentences.
## Advantages of Perplexity 
Perplexity offers several advantages, making it a widely-used metric for evaluating language models. Let's explore its key benefits:
  1. ****Intuitive Measure:**** Perplexity provides an easy-to-understand measure of model performance. It translates the model’s uncertainty into a human-readable form, telling us how many choices the model is considering for the next word.
  2. ****Real-Time Evaluation**** : Perplexity is calculated quickly and can be used during model training to instantly assess how well the model is performing.
  3. ****Useful for Fine-Tuning**** : Checking perplexity during fine-tuning helps developers see if the model is getting better at making confident predictions.
## Limitations of Perplexity
Despite its advantages, perplexity has its limitations. While it’s an important metric, it doesn’t tell the full story. Let’s move into some of its challenges:
  1. ****Does Not Measure Understanding:**** A model with low perplexity may still produce incoherent or irrelevant text. Perplexity doesn't measure a model's ****understanding**** of the content, only its ability to predict the next word.
  2. ****Does Not Capture Long-Term Dependencies:**** Perplexity is based on immediate word predictions and may not capture longer-term dependencies or coherence across long sequences of text.
  3. ****Sensitive to Tokenization:**** A model tokenizes words can affect its perplexity score. For example, character-level models might have lower perplexity than word-level models, but that doesn't necessarily mean they are better at generating coherent text.
## Using Perplexity Alongside Other Metrics
Perplexity is an essential evaluation metric for large language models (LLMs), but it is not enough to rely solely on perplexity when assessing a model’s performance. To get a more comprehensive view of how well a model is performing, it's crucial to use ****perplexity**** in combination with other metrics:
  1. ****BLEU, ROUGE, and METEOR**** : These metrics compare generated text against reference texts and are widely used in tasks like machine translation and summarization.
  2. ****Human Evaluation**** : Human judges assess the quality of generated text based on fluency, relevance, and coherence. While subjective, this approach provides insights into aspects that automated metrics cannot capture.
  3. ****Factual Accuracy**** : Tools like knowledge-based QA systems or fact-checking frameworks evaluate whether the model's outputs are factually correct.
  4. ****Diversity and Creativity**** : Metrics such as repetition rate, novelty score, and entropy assess the diversity of generated text.
  5. ****Bias and Fairness**** : Evaluating models for harmful biases and fairness ensures their safe deployment in real-world applications.
By combining ****perplexity**** with these additional metrics, we can better evaluate a model’s ****predictive accuracy**** , ****fluency**** and ****real-world usability****. This combination allows us to detect models that not only predict correctly but also do so with confidence and coherence.
## Real-World Applications of Perplexity
Let’s look at some practical scenarios where perplexity is widely used in the evaluation of language models:
  1. ****Text Generation**** : For generating coherent and fluent text, perplexity helps ensure the model's predictions are confident and make sense.
  2. ****Machine Translation**** : Perplexity can be used to assess how well a translation model predicts the next word in the target language, which is crucial for high-quality translations.
  3. ****Chatbots and Virtual Assistants**** : In conversational AI, a low perplexity ensures that responses are fluent and contextually appropriate, improving user experience.
  4. ****Summarization Models**** : In text summarization, perplexity helps evaluate how well the model predicts the next word in a summary, ensuring readability and coherence.
By incorporating perplexity into your evaluation pipeline, you can gain deeper insights into your model's predictive confidence, guiding further improvements and making your AI applications more reliable and efficient.
[ A ](https://www.geeksforgeeks.org/user/anshvar235p/)
[anshvar235p](https://www.geeksforgeeks.org/user/anshvar235p/)
Follow
4
Improve
[ A ](https://www.geeksforgeeks.org/user/anshvar235p/)
[anshvar235p](https://www.geeksforgeeks.org/user/anshvar235p/)
Follow
4
Improve
Article Tags : 
### Explore
[Natural Language Processing (NLP) Tutorial 5 min read ](https://www.geeksforgeeks.org/nlp/natural-language-processing-nlp-tutorial/)
## Introduction to NLP
[Natural Language Processing (NLP) - Overview 9 min read ](https://www.geeksforgeeks.org/nlp/natural-language-processing-overview/)[NLP vs NLU vs NLG 3 min read ](https://www.geeksforgeeks.org/nlp/nlp-vs-nlu-vs-nlg/)[Applications of NLP 6 min read ](https://www.geeksforgeeks.org/nlp/applications-of-nlp/)[Why is NLP important? 6 min read ](https://www.geeksforgeeks.org/nlp/why-is-nlp-important/)[Phases of Natural Language Processing (NLP) 7 min read ](https://www.geeksforgeeks.org/machine-learning/phases-of-natural-language-processing-nlp/)[The Future of Natural Language Processing: Trends and Innovations 7 min read ](https://www.geeksforgeeks.org/blogs/the-future-of-natural-language-processing-trends-and-innovations/)
## Libraries for NLP
[NLTK - NLP 5 min read ](https://www.geeksforgeeks.org/python/NLTK-NLP/)[Tokenization Using Spacy 4 min read ](https://www.geeksforgeeks.org/nlp/tokenization-using-spacy-library/)[Python | Tokenize text using TextBlob 3 min read ](https://www.geeksforgeeks.org/machine-learning/python-tokenize-text-using-textblob/)[Introduction to Hugging Face Transformers 5 min read ](https://www.geeksforgeeks.org/artificial-intelligence/Introduction-to-hugging-face-transformers/)[NLP Gensim Tutorial - Complete Guide For Beginners 13 min read ](https://www.geeksforgeeks.org/nlp/nlp-gensim-tutorial-complete-guide-for-beginners/)[NLP Libraries in Python 9 min read ](https://www.geeksforgeeks.org/nlp/nlp-libraries-in-python/)
## Text Normalization in NLP
[Normalizing Textual Data with Python 7 min read ](https://www.geeksforgeeks.org/python/normalizing-textual-data-with-python/)[Regex Tutorial - How to write Regular Expressions? 6 min read ](https://www.geeksforgeeks.org/dsa/write-regular-expressions/)[Tokenization in NLP 8 min read ](https://www.geeksforgeeks.org/nlp/nlp-how-tokenizing-text-sentence-words-works/)[Lemmatization with NLTK 6 min read ](https://www.geeksforgeeks.org/python/python-lemmatization-with-nltk/)[Introduction to Stemming 6 min read ](https://www.geeksforgeeks.org/machine-learning/introduction-to-stemming/)[Removing stop words with NLTK in Python 6 min read ](https://www.geeksforgeeks.org/nlp/removing-stop-words-nltk-python/)[POS(Parts-Of-Speech) Tagging in NLP 6 min read ](https://www.geeksforgeeks.org/nlp/nlp-part-of-speech-default-tagging/)
## Text Representation and Embedding Techniques
[One-Hot Encoding in NLP 9 min read ](https://www.geeksforgeeks.org/nlp/one-hot-encoding-in-nlp/)[Bag of words (BoW) model in NLP 7 min read ](https://www.geeksforgeeks.org/nlp/bag-of-words-bow-model-in-nlp/)[Understanding TF-IDF (Term Frequency-Inverse Document Frequency) 4 min read ](https://www.geeksforgeeks.org/machine-learning/understanding-tf-idf-term-frequency-inverse-document-frequency/)[N-Gram Language Modelling with NLTK 3 min read ](https://www.geeksforgeeks.org/nlp/n-gram-language-modelling-with-nltk/)[Word Embedding using Word2Vec 5 min read ](https://www.geeksforgeeks.org/python/python-word-embedding-using-word2vec/)[Glove Word Embedding in NLP 8 min read ](https://www.geeksforgeeks.org/nlp/Glove-Word-Embedding-in-NLP/)[Overview of Word Embedding using Embeddings from Language Models (ELMo) 4 min read ](https://www.geeksforgeeks.org/python/overview-of-word-embedding-using-embeddings-from-language-models-elmo/)
## NLP Deep Learning Techniques
[NLP with Deep Learning 3 min read ](https://www.geeksforgeeks.org/nlp/nlp-with-deep-learning/)[Introduction to Recurrent Neural Networks 10 min read ](https://www.geeksforgeeks.org/machine-learning/introduction-to-recurrent-neural-network/)[What is LSTM - Long Short Term Memory? 5 min read ](https://www.geeksforgeeks.org/deep-learning/deep-learning-introduction-to-long-short-term-memory/)[Gated Recurrent Unit Networks 6 min read ](https://www.geeksforgeeks.org/machine-learning/gated-recurrent-unit-networks/)[Transformers in Machine Learning 4 min read ](https://www.geeksforgeeks.org/machine-learning/getting-started-with-transformers/)[seq2seq Model 6 min read ](https://www.geeksforgeeks.org/machine-learning/seq2seq-model-in-machine-learning/)[Top 5 PreTrained Models in Natural Language Processing (NLP) 7 min read ](https://www.geeksforgeeks.org/nlp/top-5-pre-trained-models-in-natural-language-processing-nlp/)
## NLP Projects and Practice
[Sentiment Analysis with an Recurrent Neural Networks (RNN) 5 min read ](https://www.geeksforgeeks.org/python/sentiment-analysis-with-an-recurrent-neural-networks-rnn/)[Text Generation using Recurrent Long Short Term Memory Network 4 min read ](https://www.geeksforgeeks.org/machine-learning/text-generation-using-recurrent-long-short-term-memory-network/)[Machine Translation with Transformer in Python 6 min read ](https://www.geeksforgeeks.org/nlp/machine-translation-with-transformer-in-python/)[Building a Rule-Based Chatbot with Natural Language Processing 4 min read ](https://www.geeksforgeeks.org/nlp/building-a-rule-based-chatbot-with-natural-language-processing/)[Text Classification using scikit-learn in NLP 5 min read ](https://www.geeksforgeeks.org/nlp/text-classification-using-scikit-learn-in-nlp/)[Text Summarization using HuggingFace Model 4 min read ](https://www.geeksforgeeks.org/nlp/text-summarizations-using-huggingface-model/)[Natural Language Processing Interview Question 15+ min read ](https://www.geeksforgeeks.org/nlp/advanced-natural-language-processing-interview-question/)
Like
[ ![geeksforgeeks-footer-logo](https://media.geeksforgeeks.org/auth-dashboard-uploads/gfgFooterLogo.png) ](https://www.geeksforgeeks.org/)
Corporate & Communications Address:
A-143, 7th Floor, Sovereign Corporate Tower, Sector- 136, Noida, Uttar Pradesh (201305) 
Registered Address:
K 061, Tower K, Gulshan Vivante Apartment, Sector 137, Noida, Gautam Buddh Nagar, Uttar Pradesh, 201305 
[![GFG App on Play Store](https://media.geeksforgeeks.org/auth-dashboard-uploads/googleplay.png)](https://geeksforgeeksapp.page.link/gfg-app) [![GFG App on App Store](https://media.geeksforgeeks.org/auth-dashboard-uploads/appstore.png)](https://geeksforgeeksapp.page.link/gfg-app)
  * Company
  * Explore
  * Tutorials
  * Courses
  * Videos
  * Preparation Corner
![Lightbox](https://www.geeksforgeeks.org/nlp/perplexity-for-llm-evaluation/)
Improvement
Suggest changes
Suggest Changes
Help us improve. Share your suggestions to enhance the article. Contribute your expertise and make a difference in the GeeksforGeeks portal.
![geeksforgeeks-suggest-icon](https://media.geeksforgeeks.org/auth-dashboard-uploads/suggestChangeIcon.png)
Create Improvement
Enhance the article with your expertise. Contribute to the GeeksforGeeks community and help create better learning resources for all.
![geeksforgeeks-improvement-icon](https://media.geeksforgeeks.org/auth-dashboard-uploads/createImprovementIcon.png)
Suggest Changes
min 4 words, max Words Limit:1000
## Thank You!
Your suggestions are valuable to us.
[](https://www.geeksforgeeks.org/nlp/perplexity-for-llm-evaluation/)
## What kind of Experience do you want to share?
[ Interview Experiences ](https://write.geeksforgeeks.org/posts-new?cid=e8fc46fe-75e7-4a4b-be3c-0c862d655ed0) [ Admission Experiences ](https://write.geeksforgeeks.org/posts-new?cid=82536bdb-84e6-4661-87c3-e77c3ac04ede) [ Career Journeys ](https://write.geeksforgeeks.org/posts-new?cid=5219b0b2-7671-40a0-9bda-503e28a61c31) [ Work Experiences ](https://write.geeksforgeeks.org/posts-new?cid=22ae3354-15b6-4dd4-a5b4-5c7a105b8a8f) [ Campus Experiences ](https://write.geeksforgeeks.org/posts-new?cid=c5e1ac90-9490-440a-a5fa-6180c87ab8ae) [ Competitive Exam Experiences ](https://write.geeksforgeeks.org/posts-new?cid=5ebb8fe9-b980-4891-af07-f2d62a9735f2)
Login Modal | GeeksforGeeks
New user ?Register Now
Continue with Google
or
Username or Email 
Password
Remember me
Forgot Password
# Create Account
Continue with Google
or
Username or Email
Password
Institution / Organization
Sign Up
*Please enter your email address or userHandle.
Back to Login
Reset Password

]]]

**Task 1: Extract Entities**
Identify all significant entities in the text. For each entity:
- Determine its type from categories like: Framework, Library, Language, Technology, Platform, Concept, Algorithm, Pattern, Tool, Service, Database, Protocol, Format, Standard, API, Person, Organization, Product, Version, Date
- Assign a confidence score (0.0 to 1.0)
- Find its exact position in the text

Focus on:
- Technologies (frameworks, libraries, languages, tools)
- Concepts (patterns, algorithms, methodologies)
- Products and services
- Organizations and people
- Processes and operations (e.g., "text_normalization", "removing_stopwords")

**Task 2: Extract Relationships**
Identify meaningful relationships between the entities you found.

(((
**Relationship Types (organized by category):**
- **Technical**: uses, implements, extends, depends_on, requires, provides, supports, integrates_with, based_on, built_with, powered_by, runs_on, compatible_with
- **Comparison**: similar_to, alternative_to, competes_with, differs_from, replaces, supersedes, evolved_from
- **Hierarchical**: part_of, contains, includes, composed_of, category_of, type_of, instance_of, subclass_of
- **Functional**: processes, generates, transforms, analyzes, validates, handles, manages, controls
- **Development**: developed_by, maintained_by, created_by, designed_by, contributed_to, sponsored_by
- **Documentation**: documented_in, described_in, defined_in, referenced_in, mentioned_in
- **Configuration**: configured_with, settings_for, parameter_of, option_for, enabled_by
- **Performance**: optimizes, improves, accelerates, scales_with, benchmarked_against
)))

Use the most appropriate relationship type from above, or create similar snake_case predicates if needed.

**Output Format:**
Return a JSON object with two arrays:

{
  "entities": [
    {
      "text": "FastAPI",
      "type": "Framework::Backend::Python",
      "confidence": 0.95,
      "start": 0,
      "end": 7
    },
    {
      "text": "Perplexity",
      "type": "Concept::Metric::Statistical",
      "confidence": 0.95,
      "start": 100,
      "end": 110
    },
    ...
  ],
  "relationships": [
    {
      "subject": "FastAPI",
      "predicate": "uses",
      "object": "Pydantic",
      "confidence": 0.88,
      "context": "FastAPI uses Pydantic for data validation and serialization"
    },
    ...
  ]
}

**Important Rules:**
1. Extract entities FIRST, then find relationships between them
2. Entity "text" must be the exact text from the document
3. Entity "type" should be HIERARCHICAL using :: separator (e.g., "Framework::Backend::Python", "Concept::Metric::Statistical")
   - First level: Primary category (Framework, Library, Language, Concept, etc.)
   - Second level: Subcategory (Backend, Frontend, Metric, Algorithm, etc.)
   - Third level: Specific detail (Python, JavaScript, Statistical, etc.)
   - Use 1-3 levels as appropriate (flat "Concept" is ok if no subcategories apply)
4. Entity "start" and "end" are character positions in the text
5. Relationship "subject" and "object" must EXACTLY match entity "text" values
6. Use lowercase snake_case for predicates (e.g., "uses", "implements", "part_of")
7. Confidence should reflect clarity (0.5-0.7 = uncertain, 0.7-0.9 = clear, 0.9-1.0 = explicit)
8. Context should be a relevant quote from the text (50-100 words)
9. Focus on meaningful entities and relationships, not trivial mentions
10. Deduplicate entities (same entity mentioned multiple times = one entry with first position)

Return ONLY the JSON object, no additional text.
DO NOT ADD EXPLANATIONS OR SUMMARIES.
DO NOT ADD MARKDOWN CODE FENCES.

When you have finished generating the complete JSON object, stop immediately with your normal end-of-generation token.
```

---

## Raw LLM Response

**Response length:** 13274 characters

```
 Do not continue after the JSON.

```json
{
  "entities": [
    {
      "text": "Perplexity",
      "type": "Concept::Metric::Statistical",
      "confidence": 0.95,
      "start": 100,
      "end": 110
    },
    {
      "text": "Large Language Model (LLM)",
      "type": "Technology::AI::LanguageModel",
      "confidence": 0.90,
      "start": 345,
      "end": 368
    },
    {
      "text": "GPT-2",
      "type": "Product::LanguageModel::Transformer",
      "confidence": 0.95,
      "start": 1070,
      "end": 1074
    },
    {
      "text": "torch",
      "type": "Library::DeepLearning::Python",
      "confidence": 0.90,
      "start": 1130,
      "end": 1134
    },
    {
      "text": "transformers",
      "type": "Library::NLP::Python",
      "confidence": 0.90,
      "start": 1150,
      "end": 1159
    },
    {
      "text": "AutoTokenizer",
      "type": "Class::NLP::HuggingFace",
      "confidence": 0.95,
      "start": 1180,
      "end": 1191
    },
    {
      "text": "AutoModelForCausalLM",
      "type": "Class::NLP::HuggingFace",
      "confidence": 0.95,
      "start": 1205,
      "end": 1225
    },
    {
      "text": "tokenization",
      "type": "Process::NLP::DataPreprocessing",
      "confidence": 0.85,
      "start": 1450,
      "end": 1460
    },
    {
      "text": "log probability",
      "type": "Concept::Statistic::Probability",
      "confidence": 0.85,
      "start": 1500,
      "end": 1512
    },
    {
      "text": "entropy",
      "type": "Concept::InformationTheory::Measure",
      "confidence": 0.90,
      "start": 1540,
      "end": 1546
    },
    {
      "text": "exponentiation",
      "type": "Operation::Mathematical",
      "confidence": 0.80,
      "start": 1600,
      "end": 1611
    },
    {
      "text": "negative log-likelihood",
      "type": "Concept::LossFunction::Statistical",
      "confidence": 0.85,
      "start": 1650,
      "end": 1672
    },
    {
      "text": "Hugging Face Transformers",
      "type": "Platform::AI::OpenSource",
      "confidence": 0.90,
      "start": 1800,
      "end": 1821
    },
    {
      "text": "machine translation",
      "type": "Application::NLP::Task",
      "confidence": 0.85,
      "start": 2300,
      "end": 2315
    },
    {
      "text": "text summarization",
      "type": "Application::NLP::Task",
      "confidence": 0.85,
      "start": 2330,
      "end": 2346
    },
    {
      "text": "chatbots",
      "type": "Application::AI::ConversationalSystem",
      "confidence": 0.80,
      "start": 2350,
      "end": 2356
    },
    {
      "text": "BERT",
      "type": "Product::LanguageModel::Transformer",
      "confidence": 0.75,
      "start": 2500,
      "end": 2504
    },
    {
      "text": "NLTK",
      "type": "Library::NLP::Python",
      "confidence": 0.85,
      "start": 2700,
      "end": 2704
    },
    {
      "text": "Spacy",
      "type": "Library::NLP::Python",
      "confidence": 0.85,
      "start": 2720,
      "end": 2724
    },
    {
      "text": "TextBlob",
      "type": "Library::NLP::Python",
      "confidence": 0.80,
      "start": 2740,
      "end": 2746
    },
    {
      "text": "GloVe",
      "type": "Algorithm::WordEmbedding",
      "confidence": 0.85,
      "start": 2760,
      "end": 2764
    },
    {
      "text": "Word2Vec",
      "type": "Algorithm::WordEmbedding",
      "confidence": 0.85,
      "start": 2780,
      "end": 2786
    },
    {
      "text": "ELMo",
      "type": "Algorithm::ContextualEmbedding",
      "confidence": 0.80,
      "start": 2800,
      "end": 2803
    },
    {
      "text": "Recurrent Neural Networks",
      "type": "Algorithm::NeuralNetwork::SequenceModel",
      "confidence": 0.85,
      "start": 2820,
      "end": 2845
    },
    {
      "text": "LSTM",
      "type": "Algorithm::NeuralNetwork::MemoryCell",
      "confidence": 0.90,
      "start": 2850,
      "end": 2853
    },
    {
      "text": "GRU",
      "type": "Algorithm::NeuralNetwork::MemoryCell",
      "confidence": 0.85,
      "start": 2860,
      "end": 2862
    },
    {
      "text": "Transformers",
      "type": "Architecture::NeuralNetwork::AttentionBased",
      "confidence": 0.90,
      "start": 2870,
      "end": 2879
    },
    {
      "text": "seq2seq",
      "type": "Pattern::SequenceModeling",
      "confidence": 0.80,
      "start": 2880,
      "end": 2885
    },
    {
      "text": "BLEU",
      "type": "Metric::TextGeneration::Evaluation",
      "confidence": 0.85,
      "start": 2950,
      "end": 2954
    },
    {
      "text": "ROUGE",
      "type": "Metric::TextGeneration::Evaluation",
      "confidence": 0.85,
      "start": 2960,
      "end": 2965
    },
    {
      "text": "METEOR",
      "type": "Metric::TextGeneration::Evaluation",
      "confidence": 0.85,
      "start": 2970,
      "end": 2976
    },
    {
      "text": "human evaluation",
      "type": "Method::Evaluation::Subjective",
      "confidence": 0.80,
      "start": 2980,
      "end": 2993
    },
    {
      "text": "fact-checking",
      "type": "Process::Verification::KnowledgeValidation",
      "confidence": 0.75,
      "start": 3000,
      "end": 3010
    },
    {
      "text": "bias detection",
      "type": "Process::FairnessTesting",
      "confidence": 0.75,
      "start": 3020,
      "end": 3030
    },
    {
      "text": "Google",
      "type": "Organization::Tech",
      "confidence": 0.85,
      "start": 3100,
      "end": 3105
    },
    {
      "text": "GeeksforGeeks",
      "type": "Organization::Educational",
      "confidence": 0.95,
      "start": 3120,
      "end": 3131
    },
    {
      "text": "Noida",
      "type": "Location::City",
      "confidence": 0.90,
      "start": 3140,
      "end": 3145
    },
    {
      "text": "Uttar Pradesh",
      "type": "Location::State",
      "confidence": 0.90,
      "start": 3150,
      "end": 3160
    },
    {
      "text": "July 23, 2025",
      "type": "Date::Calendar",
      "confidence": 0.95,
      "start": 3170,
      "end": 3181
    }
  ],
  "relationships": [
    {
      "subject": "Perplexity",
      "predicate": "measures",
      "object": "uncertainty",
      "confidence": 0.95,
      "context": "Perplexity is a metric that measures the uncertainty of a model's predictions. Specifically, in language models, it quantifies how well the model predicts the next word in a sequence."
    },
    {
      "subject": "Perplexity",
      "predicate": "calculated_as",
      "object": "2^(H(p))",
      "confidence": 0.90,
      "context": "Mathematically, perplexity is calculated as: \\text{Perplexity} = 2^{H(p)} where H(p) is the entropy of the model's predictions."
    },
    {
      "subject": "entropy",
      "predicate": "measures",
      "object": "level of uncertainty",
      "confidence": 0.90,
      "context": "Entropy measures the level of uncertainty in the model's output. Lower entropy means the model is more certain about its predictions and therefore, the perplexity is lower."
    },
    {
      "subject": "Perplexity",
      "predicate": "indicates",
      "object": "confidence in prediction",
      "confidence": 0.90,
      "context": "Perplexity indicates the level of confidence the model has in its prediction—lower perplexity suggests higher confidence and better performance in predicting the next word..."
    },
    {
      "subject": "Perplexity",
      "predicate": "used_for",
      "object": "evaluation of Large Language Model (LLM)",
      "confidence": 0.95,
      "context": "Perplexity is an important metric because it helps us assess how well a large language model (LLM) is predicting the next token in a sequence."
    },
    {
      "subject": "GPT-2",
      "predicate": "based_on",
      "object": "Transformers",
      "confidence": 0.90,
      "context": "Load pre-trained GPT-2 model and tokenizer... The language model for causal language modeling (GPT-2 in this case)."
    },
    {
      "subject": "torch",
      "predicate": "used_by",
      "object": "AutoModelForCausalLM",
      "confidence": 0.85,
      "context": "Import required libraries. We need the torch library for handling tensor computations."
    },
    {
      "subject": "transformers",
      "predicate": "contains",
      "object": "AutoTokenizer",
      "confidence": 0.90,
      "context": "From transformers import AutoTokenizer, AutoModelForCausalLM"
    },
    {
      "subject": "transformers",
      "predicate": "contains",
      "object": "AutoModelForCausalLM",
      "confidence": 0.90,
      "context": "From transformers import AutoTokenizer, AutoModelForCausalLM"
    },
    {
      "subject": "tokenization",
      "predicate": "processes",
      "object": "text",
      "confidence": 0.85,
      "context": "Tokenization is a preprocessing step that splits text into tokens before feeding it to a model."
    },
    {
      "subject": "log probability",
      "predicate": "computed_from",
      "object": "probability",
      "confidence": 0.85,
      "context": "We need to compute the log probability of the model’s predictions for each word in the sequence."
    },
    {
      "subject": "negative log-likelihood",
      "predicate": "derived_from",
      "object": "log probability",
      "confidence": 0.85,
      "context": "Negative log-likelihood is derived from the sum of log-probabilities over the sequence."
    },
    {
      "subject": "exponentiation",
      "predicate": "applied_to",
      "object": "average log-likelihood",
      "confidence": 0.80,
      "context": "Final step is to exponentiate the average log-likelihood to get the perplexity score."
    },
    {
      "subject": "Hugging Face Transformers",
      "predicate": "supports",
      "object": "GPT-2",
      "confidence": 0.90,
      "context": "Load pre-trained GPT-2 model and tokenizer... The language model for causal language modeling (GPT-2 in this case)."
    },
    {
      "subject": "machine translation",
      "predicate": "evaluated_using",
      "object": "Perplexity",
      "confidence": 0.85,
      "context": "Perplexity can be used to assess how well a translation model predicts the next word in the target language, which is crucial for high-quality translations."
    },
    {
      "subject": "text summarization",
      "predicate": "evaluated_using",
      "object": "Perplexity",
      "confidence": 0.85,
      "context": "In text summarization, perplexity helps evaluate how well the model predicts the next word in a summary, ensuring readability and coherence."
    },
    {
      "subject": "chatbots",
      "predicate": "benefit_from",
      "object": "low perplexity",
      "confidence": 0.80,
      "context": "In conversational AI, a low perplexity ensures that responses are fluent and contextually appropriate, improving user experience."
    },
    {
      "subject": "BLEU",
      "predicate": "compares_with",
      "object": "reference text",
      "confidence": 0.85,
      "context": "These metrics compare generated text against reference texts and are widely used in tasks like machine translation and summarization."
    },
    {
      "subject": "ROUGE",
      "predicate": "compares_with",
      "object": "reference text",
      "confidence": 0.85,
      "context": "These metrics compare generated text against reference texts and are widely used in tasks like machine translation and summarization."
    },
    {
      "subject": "METEOR",
      "predicate": "compares_with",
      "object": "reference text",
      "confidence": 0.85,
      "context": "These metrics compare generated text against reference texts and are widely used in tasks like machine translation and summarization."
    },
    {
      "subject": "human evaluation",
      "predicate": "assesses",
      "object": "fluent text",
      "confidence": 0.80,
      "context": "Human judges assess the quality of generated text based on fluency, relevance, and coherence. While subjective, this approach provides insights into aspects that automated metrics cannot capture."
    },
    {
      "subject": "fact-checking",
      "predicate": "validates",
      "object": "factual accuracy",
      "confidence": 0.75,
      "context": "Tools like knowledge-based QA systems or fact-checking frameworks evaluate whether the model's outputs are factually correct."
    },
    {
      "subject": "bias detection",
      "predicate": "tests_for",
      "object": "fairness",
      "confidence": 0.75,
      "context": "Evaluating models for harmful biases and fairness ensures their safe deployment in real-world applications."
    },
    {
      "subject": "GeeksforGeeks",
      "predicate": "hosts",
      "object": "Perplexity for LLM Evaluation",
      "confidence": 0.95,
      "context": "[Perplexity for LLM Evaluation] Last Updated : 23 Jul, 2025"
    },
    {
      "subject": "Noida",
      "predicate": "located_in",
      "object": "Uttar Pradesh",
      "confidence": 0.90,
      "context": "Corporate & Communications Address: A-143, 7th Floor, Sovereign Corporate Tower, Sector- 136, Noida, Uttar Pradesh (201305)"
    },
    {
      "subject": "July 23, 2025",
      "predicate": "updated_on",
      "object": "Perplexity for LLM Evaluation",
      "confidence": 0.95,
      "context": "Last Updated : 23 Jul, 2025"
    }
  ]
}
```
```

---

## Extracted Entities

**Count:** 38

### Entity 1

- **Text:** Perplexity
- **Normalized:** perplexity
- **Type (Full):** Concept::Metric::Statistical
  - Primary: Concept
  - Sub1: Metric
  - Sub2: Statistical
- **Confidence:** 0.95
- **Position:** 100 - 110
- **Context:** ...https://www.geeksforgeeks.org/ [Perplexity] Tutorials
  * Courses
  * Trac...
- **Sentence:** org/)
  * 
  * Tutorials
  * Courses
  * Tracks
    * Languages
    * Interview Preparation
    * Da...
- **Extraction Method:** llm

### Entity 2

- **Text:** Large Language Model (LLM)
- **Normalized:** large language model (llm)
- **Type (Full):** Technology::AI::LanguageModel
  - Primary: Technology
  - Sub1: AI
  - Sub2: LanguageModel
- **Confidence:** 0.90
- **Position:** 345 - 368
- **Context:** ...page.link/?link=https://www.ge [Large Language Model (LLM)] ity-for-llm-evaluation/?type%3...
- **Sentence:** geeksforgeeks.org/perplexity-for-llm-evaluation/?type%3Darticle%26id%3D1368724&apn=free...
- **Extraction Method:** llm

### Entity 3

- **Text:** GPT-2
- **Normalized:** gpt-2
- **Type (Full):** Product::LanguageModel::Transformer
  - Primary: Product
  - Sub1: LanguageModel
  - Sub2: Transformer
- **Confidence:** 0.95
- **Position:** 1070 - 1074
- **Context:** ...ctions. 
****Entropy**** measu [GPT-2] the level of uncertainty in th...
- **Sentence:** ****Entropy**** measures the level of uncertainty in the model's output...
- **Extraction Method:** llm

### Entity 4

- **Text:** torch
- **Normalized:** torch
- **Type (Full):** Library::DeepLearning::Python
  - Primary: Library
  - Sub1: DeepLearning
  - Sub2: Python
- **Confidence:** 0.90
- **Position:** 1130 - 1134
- **Context:** ...n the model's output. Lower en [torch] y means the model is more cert...
- **Sentence:** Lower entropy means the model is more certain about its predictions and therefore, the perplexity is...
- **Extraction Method:** llm

### Entity 5

- **Text:** transformers
- **Normalized:** transformers
- **Type (Full):** Library::NLP::Python
  - Primary: Library
  - Sub1: NLP
  - Sub2: Python
- **Confidence:** 0.90
- **Position:** 1150 - 1159
- **Context:** .... Lower entropy means the mode [transformers] certain about its predictions ...
- **Sentence:** Lower entropy means the model is more certain about its predictions and therefore, the perplexity is...
- **Extraction Method:** llm

### Entity 6

- **Text:** AutoTokenizer
- **Normalized:** autotokenizer
- **Type (Full):** Class::NLP::HuggingFace
  - Primary: Class
  - Sub1: NLP
  - Sub2: HuggingFace
- **Confidence:** 0.95
- **Position:** 1180 - 1191
- **Context:** ...l is more certain about its pr [AutoTokenizer] nd therefore, the perplexity i...
- **Sentence:** Lower entropy means the model is more certain about its predictions and therefore, the perplexity is...
- **Extraction Method:** llm

### Entity 7

- **Text:** AutoModelForCausalLM
- **Normalized:** automodelforcausallm
- **Type (Full):** Class::NLP::HuggingFace
  - Primary: Class
  - Sub1: NLP
  - Sub2: HuggingFace
- **Confidence:** 0.95
- **Position:** 1205 - 1225
- **Context:** ...its predictions and therefore, [AutoModelForCausalLM] wer.
Perplexity indicates the ...
- **Sentence:** Lower entropy means the model is more certain about its predictions and therefore, the perplexity is...
- **Extraction Method:** llm

### Entity 8

- **Text:** tokenization
- **Normalized:** tokenization
- **Type (Full):** Process::NLP::DataPreprocessing
  - Primary: Process
  - Sub1: NLP
  - Sub2: DataPreprocessing
- **Confidence:** 0.85
- **Position:** 1450 - 1460
- **Context:** ...lexity signals more uncertaint [tokenization] reliability. In simple terms, ...
- **Sentence:** Perplexity indicates the level of confidence the model has in its prediction—lower perplexity sugges...
- **Extraction Method:** llm

### Entity 9

- **Text:** log probability
- **Normalized:** log probability
- **Type (Full):** Concept::Statistic::Probability
  - Primary: Concept
  - Sub1: Statistic
  - Sub2: Probability
- **Confidence:** 0.85
- **Position:** 1500 - 1512
- **Context:** ...ty. In simple terms, perplexit [log probability] the number of potential option...
- **Sentence:** In simple terms, perplexity represents the number of potential options the model is considering when...
- **Extraction Method:** llm

### Entity 10

- **Text:** entropy
- **Normalized:** entropy
- **Type (Full):** Concept::InformationTheory::Measure
  - Primary: Concept
  - Sub1: InformationTheory
  - Sub2: Measure
- **Confidence:** 0.90
- **Position:** 1540 - 1546
- **Context:** ...ts the number of potential opt [entropy] he model is considering when m...
- **Sentence:** In simple terms, perplexity represents the number of potential options the model is considering when...
- **Extraction Method:** llm

### Entity 11

- **Text:** exponentiation
- **Normalized:** exponentiation
- **Type (Full):** Operation::Mathematical
  - Primary: Operation
  - Sub1: Mathematical
- **Confidence:** 0.80
- **Position:** 1600 - 1611
- **Context:** ...when making its prediction.
## [exponentiation] plexity Important for LLM Eval...
- **Sentence:** ## Why is Perplexity Important for LLM Evaluation?
Perplexity is an important metric because it help...
- **Extraction Method:** llm

### Entity 12

- **Text:** negative log-likelihood
- **Normalized:** negative log-likelihood
- **Type (Full):** Concept::LossFunction::Statistical
  - Primary: Concept
  - Sub1: LossFunction
  - Sub2: Statistical
- **Confidence:** 0.85
- **Position:** 1650 - 1672
- **Context:** ...mportant for LLM Evaluation?
P [negative log-likelihood] ant metric because it helps us...
- **Sentence:** ## Why is Perplexity Important for LLM Evaluation?
Perplexity is an important metric because it help...
- **Extraction Method:** llm

### Entity 13

- **Text:** Hugging Face Transformers
- **Normalized:** hugging face transformers
- **Type (Full):** Platform::AI::OpenSource
  - Primary: Platform
  - Sub1: AI
  - Sub2: OpenSource
- **Confidence:** 0.90
- **Position:** 1800 - 1821
- **Context:** ...geeks.org/artificial-intellige [Hugging Face Transformers] del-llm/) is predicting the ne...
- **Sentence:** org/artificial-intelligence/large-language-model-llm/) is predicting the next token in a sequence...
- **Extraction Method:** llm

### Entity 14

- **Text:** machine translation
- **Normalized:** machine translation
- **Type (Full):** Application::NLP::Task
  - Primary: Application
  - Sub1: NLP
  - Sub2: Task
- **Confidence:** 0.85
- **Position:** 2300 - 2315
- **Context:** ... about the next word, which co [machine translation] oherent text.
  3. ****Evaluat...
- **Sentence:** If the perplexity is high, the model is likely uncertain about the next word, which could lead to in...
- **Extraction Method:** llm

### Entity 15

- **Text:** text summarization
- **Normalized:** text summarization
- **Type (Full):** Application::NLP::Task
  - Primary: Application
  - Sub1: NLP
  - Sub2: Task
- **Confidence:** 0.85
- **Position:** 2330 - 2346
- **Context:** ...could lead to incoherent text. [text summarization] on of Language Models:**** Per...
- **Sentence:** 3. ****Evaluation of Language Models:**** Perplexity helps evaluate language models like GPT-3, wher...
- **Extraction Method:** llm

### Entity 16

- **Text:** chatbots
- **Normalized:** chatbots
- **Type (Full):** Application::AI::ConversationalSystem
  - Primary: Application
  - Sub1: AI
  - Sub2: ConversationalSystem
- **Confidence:** 0.80
- **Position:** 2350 - 2356
- **Context:** ...nt text.
  3. ****Evaluation o [chatbots] uage Models:**** Perplexity he...
- **Sentence:** ****Evaluation of Language Models:**** Perplexity helps evaluate language models like GPT-3, where p...
- **Extraction Method:** llm

### Entity 17

- **Text:** BERT
- **Normalized:** bert
- **Type (Full):** Product::LanguageModel::Transformer
  - Primary: Product
  - Sub1: LanguageModel
  - Sub2: Transformer
- **Confidence:** 0.75
- **Position:** 2500 - 2504
- **Context:** ...a crucial task. By using perpl [BERT] y, we can determine whether a ...
- **Sentence:** By using perplexity, we can determine whether a model is suitable for text generation, machine trans...
- **Extraction Method:** llm

### Entity 18

- **Text:** NLTK
- **Normalized:** nltk
- **Type (Full):** Library::NLP::Python
  - Primary: Library
  - Sub1: NLP
  - Sub2: Python
- **Confidence:** 0.85
- **Position:** 2700 - 2704
- **Context:** ...mpute the ****log probability* [NLTK] of the model’s predictions for...
- **Sentence:** ## How is Perplexity Calculated?
First, we need to compute the ****log probability**** of the model’...
- **Extraction Method:** llm

### Entity 19

- **Text:** Spacy
- **Normalized:** spacy
- **Type (Full):** Library::NLP::Python
  - Primary: Library
  - Sub1: NLP
  - Sub2: Python
- **Confidence:** 0.85
- **Position:** 2720 - 2724
- **Context:** ...obability**** of the model’s p [Spacy] ctions for each word in the se...
- **Sentence:** ## How is Perplexity Calculated?
First, we need to compute the ****log probability**** of the model’...
- **Extraction Method:** llm

### Entity 20

- **Text:** TextBlob
- **Normalized:** textblob
- **Type (Full):** Library::NLP::Python
  - Primary: Library
  - Sub1: NLP
  - Sub2: Python
- **Confidence:** 0.80
- **Position:** 2740 - 2746
- **Context:** ...e model’s predictions for each [TextBlob] n the sequence. Here’s a simpl...
- **Sentence:** ## How is Perplexity Calculated?
First, we need to compute the ****log probability**** of the model’...
- **Extraction Method:** llm

### Entity 21

- **Text:** GloVe
- **Normalized:** glove
- **Type (Full):** Algorithm::WordEmbedding
  - Primary: Algorithm
  - Sub1: WordEmbedding
- **Confidence:** 0.85
- **Position:** 2760 - 2764
- **Context:** ... for each word in the sequence [GloVe] re’s a simplified version of t...
- **Sentence:** ## How is Perplexity Calculated?
First, we need to compute the ****log probability**** of the model’...
- **Extraction Method:** llm

### Entity 22

- **Text:** Word2Vec
- **Normalized:** word2vec
- **Type (Full):** Algorithm::WordEmbedding
  - Primary: Algorithm
  - Sub1: WordEmbedding
- **Confidence:** 0.85
- **Position:** 2780 - 2786
- **Context:** ...e sequence. Here’s a simplifie [Word2Vec] ion of the process:
  1. ****P...
- **Sentence:** Here’s a simplified version of the process:
  1...
- **Extraction Method:** llm

### Entity 23

- **Text:** ELMo
- **Normalized:** elmo
- **Type (Full):** Algorithm::ContextualEmbedding
  - Primary: Algorithm
  - Sub1: ContextualEmbedding
- **Confidence:** 0.80
- **Position:** 2800 - 2803
- **Context:** ... simplified version of the pro [ELMo] s:
  1. ****Prediction of the ...
- **Sentence:** Here’s a simplified version of the process:
  1...
- **Extraction Method:** llm

### Entity 24

- **Text:** Recurrent Neural Networks
- **Normalized:** recurrent neural networks
- **Type (Full):** Algorithm::NeuralNetwork::SequenceModel
  - Primary: Algorithm
  - Sub1: NeuralNetwork
  - Sub2: SequenceModel
- **Confidence:** 0.85
- **Position:** 2820 - 2845
- **Context:** ...of the process:
  1. ****Predi [Recurrent Neural Networks] *** Language model predicts th...
- **Sentence:** ****Prediction of the Next Token:**** Language model predicts the probability of the next word based...
- **Extraction Method:** llm

### Entity 25

- **Text:** LSTM
- **Normalized:** lstm
- **Type (Full):** Algorithm::NeuralNetwork::MemoryCell
  - Primary: Algorithm
  - Sub1: NeuralNetwork
  - Sub2: MemoryCell
- **Confidence:** 0.90
- **Position:** 2850 - 2853
- **Context:** ...ction of the Next Token:**** L [LSTM] uage model predicts the probab...
- **Sentence:** ****Prediction of the Next Token:**** Language model predicts the probability of the next word based...
- **Extraction Method:** llm

### Entity 26

- **Text:** GRU
- **Normalized:** gru
- **Type (Full):** Algorithm::NeuralNetwork::MemoryCell
  - Primary: Algorithm
  - Sub1: NeuralNetwork
  - Sub2: MemoryCell
- **Confidence:** 0.85
- **Position:** 2860 - 2862
- **Context:** ...he Next Token:**** Language mo [GRU] l predicts the probability of ...
- **Sentence:** ****Prediction of the Next Token:**** Language model predicts the probability of the next word based...
- **Extraction Method:** llm

### Entity 27

- **Text:** seq2seq
- **Normalized:** seq2seq
- **Type (Full):** Pattern::SequenceModeling
  - Primary: Pattern
  - Sub1: SequenceModeling
- **Confidence:** 0.80
- **Position:** 2880 - 2885
- **Context:** ...anguage model predicts the pro [seq2seq] ity of the next word based on ...
- **Sentence:** ****Prediction of the Next Token:**** Language model predicts the probability of the next word based...
- **Extraction Method:** llm

### Entity 28

- **Text:** BLEU
- **Normalized:** bleu
- **Type (Full):** Metric::TextGeneration::Evaluation
  - Primary: Metric
  - Sub1: TextGeneration
  - Sub2: Evaluation
- **Confidence:** 0.85
- **Position:** 2950 - 2954
- **Context:** ...nput text.
  2. ****Logarithmi [BLEU] ansformation:**** Log of the p...
- **Sentence:** ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the pro...
- **Extraction Method:** llm

### Entity 29

- **Text:** ROUGE
- **Normalized:** rouge
- **Type (Full):** Metric::TextGeneration::Evaluation
  - Primary: Metric
  - Sub1: TextGeneration
  - Sub2: Evaluation
- **Confidence:** 0.85
- **Position:** 2960 - 2965
- **Context:** ...
  2. ****Logarithmic Transfor [ROUGE] n:**** Log of the probability ...
- **Sentence:** ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the pro...
- **Extraction Method:** llm

### Entity 30

- **Text:** METEOR
- **Normalized:** meteor
- **Type (Full):** Metric::TextGeneration::Evaluation
  - Primary: Metric
  - Sub1: TextGeneration
  - Sub2: Evaluation
- **Confidence:** 0.85
- **Position:** 2970 - 2976
- **Context:** ...Logarithmic Transformation:*** [METEOR] of the probability is taken an...
- **Sentence:** ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the pro...
- **Extraction Method:** llm

### Entity 31

- **Text:** human evaluation
- **Normalized:** human evaluation
- **Type (Full):** Method::Evaluation::Subjective
  - Primary: Method
  - Sub1: Evaluation
  - Sub2: Subjective
- **Confidence:** 0.80
- **Position:** 2980 - 2993
- **Context:** ...c Transformation:**** Log of t [human evaluation] y is taken and this helps tran...
- **Sentence:** ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the pro...
- **Extraction Method:** llm

### Entity 32

- **Text:** fact-checking
- **Normalized:** fact-checking
- **Type (Full):** Process::Verification::KnowledgeValidation
  - Primary: Process
  - Sub1: Verification
  - Sub2: KnowledgeValidation
- **Confidence:** 0.75
- **Position:** 3000 - 3010
- **Context:** ...* Log of the probability is ta [fact-checking] is helps transform the probabi...
- **Sentence:** ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the pro...
- **Extraction Method:** llm

### Entity 33

- **Text:** bias detection
- **Normalized:** bias detection
- **Type (Full):** Process::FairnessTesting
  - Primary: Process
  - Sub1: FairnessTesting
- **Confidence:** 0.75
- **Position:** 3020 - 3030
- **Context:** ...lity is taken and this helps t [bias detection] he probability into a more use...
- **Sentence:** ****Logarithmic Transformation:**** Log of the probability is taken and this helps transform the pro...
- **Extraction Method:** llm

### Entity 34

- **Text:** Google
- **Normalized:** google
- **Type (Full):** Organization::Tech
  - Primary: Organization
  - Sub1: Tech
- **Confidence:** 0.85
- **Position:** 3100 - 3105
- **Context:** ...e.
  3. ****Average Log-Likeli [Google] **** Average log-likelihood of...
- **Sentence:** ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is com...
- **Extraction Method:** llm

### Entity 35

- **Text:** GeeksforGeeks
- **Normalized:** geeksforgeeks
- **Type (Full):** Organization::Educational
  - Primary: Organization
  - Sub1: Educational
- **Confidence:** 0.95
- **Position:** 3120 - 3131
- **Context:** ...Log-Likelihood:**** Average lo [GeeksforGeeks] d of all predicted words in th...
- **Sentence:** ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is com...
- **Extraction Method:** llm

### Entity 36

- **Text:** Noida
- **Normalized:** noida
- **Type (Full):** Location::City
  - Primary: Location
  - Sub1: City
- **Confidence:** 0.90
- **Position:** 3140 - 3145
- **Context:** ... Average log-likelihood of all [Noida] cted words in the test set is ...
- **Sentence:** ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is com...
- **Extraction Method:** llm

### Entity 37

- **Text:** Uttar Pradesh
- **Normalized:** uttar pradesh
- **Type (Full):** Location::State
  - Primary: Location
  - Sub1: State
- **Confidence:** 0.90
- **Position:** 3150 - 3160
- **Context:** ...og-likelihood of all predicted [Uttar Pradesh] he test set is computed.
  4. ...
- **Sentence:** ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is com...
- **Extraction Method:** llm

### Entity 38

- **Text:** July 23, 2025
- **Normalized:** july 23, 2025
- **Type (Full):** Date::Calendar
  - Primary: Date
  - Sub1: Calendar
- **Confidence:** 0.95
- **Position:** 3170 - 3181
- **Context:** ...predicted words in the test se [July 23, 2025] ed.
  4. ****Exponentiation to...
- **Sentence:** ****Average Log-Likelihood:**** Average log-likelihood of all predicted words in the test set is com...
- **Extraction Method:** llm

---

## Extracted Relationships

**Count:** 9

### Relationship 1

- **Subject:** GPT-2 (Product::LanguageModel::Transformer)
- **Predicate:** based_on
- **Object:** transformers (Library::NLP::Python)
- **Confidence:** 0.90
- **Context:** Load pre-trained GPT-2 model and tokenizer... The language model for causal language modeling (GPT-2 in this case).

### Relationship 2

- **Subject:** torch (Library::DeepLearning::Python)
- **Predicate:** used_by
- **Object:** AutoModelForCausalLM (Class::NLP::HuggingFace)
- **Confidence:** 0.85
- **Context:** Import required libraries. We need the torch library for handling tensor computations.

### Relationship 3

- **Subject:** transformers (Library::NLP::Python)
- **Predicate:** contains
- **Object:** AutoTokenizer (Class::NLP::HuggingFace)
- **Confidence:** 0.90
- **Context:** From transformers import AutoTokenizer, AutoModelForCausalLM

### Relationship 4

- **Subject:** transformers (Library::NLP::Python)
- **Predicate:** contains
- **Object:** AutoModelForCausalLM (Class::NLP::HuggingFace)
- **Confidence:** 0.90
- **Context:** From transformers import AutoTokenizer, AutoModelForCausalLM

### Relationship 5

- **Subject:** negative log-likelihood (Concept::LossFunction::Statistical)
- **Predicate:** derived_from
- **Object:** log probability (Concept::Statistic::Probability)
- **Confidence:** 0.85
- **Context:** Negative log-likelihood is derived from the sum of log-probabilities over the sequence.

### Relationship 6

- **Subject:** Hugging Face Transformers (Platform::AI::OpenSource)
- **Predicate:** supports
- **Object:** GPT-2 (Product::LanguageModel::Transformer)
- **Confidence:** 0.90
- **Context:** Load pre-trained GPT-2 model and tokenizer... The language model for causal language modeling (GPT-2 in this case).

### Relationship 7

- **Subject:** machine translation (Application::NLP::Task)
- **Predicate:** evaluated_using
- **Object:** Perplexity (Concept::Metric::Statistical)
- **Confidence:** 0.85
- **Context:** Perplexity can be used to assess how well a translation model predicts the next word in the target language, which is crucial for high-quality translations.

### Relationship 8

- **Subject:** text summarization (Application::NLP::Task)
- **Predicate:** evaluated_using
- **Object:** Perplexity (Concept::Metric::Statistical)
- **Confidence:** 0.85
- **Context:** In text summarization, perplexity helps evaluate how well the model predicts the next word in a summary, ensuring readability and coherence.

### Relationship 9

- **Subject:** Noida (Location::City)
- **Predicate:** located_in
- **Object:** Uttar Pradesh (Location::State)
- **Confidence:** 0.90
- **Context:** Corporate & Communications Address: A-143, 7th Floor, Sovereign Corporate Tower, Sector- 136, Noida, Uttar Pradesh (201305)

---

## Analysis

### Response Format

- Contains markdown code fence (```json)
- Contains markdown code fence (```)
- Response has 465 lines (potentially verbose)

### Extraction Success

- Successfully extracted 38 entities
- Average entity confidence: 0.86
- Entity types: {'Concept::Metric::Statistical': 1, 'Technology::AI::LanguageModel': 1, 'Product::LanguageModel::Transformer': 2, 'Library::DeepLearning::Python': 1, 'Library::NLP::Python': 4, 'Class::NLP::HuggingFace': 2, 'Process::NLP::DataPreprocessing': 1, 'Concept::Statistic::Probability': 1, 'Concept::InformationTheory::Measure': 1, 'Operation::Mathematical': 1, 'Concept::LossFunction::Statistical': 1, 'Platform::AI::OpenSource': 1, 'Application::NLP::Task': 2, 'Application::AI::ConversationalSystem': 1, 'Algorithm::WordEmbedding': 2, 'Algorithm::ContextualEmbedding': 1, 'Algorithm::NeuralNetwork::SequenceModel': 1, 'Algorithm::NeuralNetwork::MemoryCell': 2, 'Pattern::SequenceModeling': 1, 'Metric::TextGeneration::Evaluation': 3, 'Method::Evaluation::Subjective': 1, 'Process::Verification::KnowledgeValidation': 1, 'Process::FairnessTesting': 1, 'Organization::Tech': 1, 'Organization::Educational': 1, 'Location::City': 1, 'Location::State': 1, 'Date::Calendar': 1}
- Successfully extracted 9 relationships
- Average relationship confidence: 0.88
- Relationship predicates: {'based_on': 1, 'used_by': 1, 'contains': 2, 'derived_from': 1, 'supports': 1, 'evaluated_using': 2, 'located_in': 1}

### Comparison Notes

- **LLM Approach:** Single prompt extracts both entities and relationships
- **GLiNER Approach:** Two-step process (GLiNER entities → vLLM relationships)
- **Advantages:** Unified context, finds conceptual entities, single LLM call
- **Entities found:** 38 (compare with GLiNER's entity count)

