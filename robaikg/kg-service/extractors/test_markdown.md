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
