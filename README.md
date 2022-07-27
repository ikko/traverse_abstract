# Traverse Abstract

This experiment summarizes scientific papers using Natural Language Processing. The idea is to create an aggregator that can be viewed on mobile phones and directs to the Paper contents itself for detailed study.

## NLP
Uses distilbart-cnn-12-6 model from huggingface. We do not process all content since it is resource consuming. Machine Learning, Artificial Intelligence and Computational Complexity have priority.

## Data Soucre
Fetches [arxiv.org](https://arxiv.org) for summary text, paper and images.

## Web
Uses Flask to generate site content, all data is cached into html files for security and fast performance.

## Demo
You can catch a somewhat outdated version at [traverse.depth.hu](https://traverse.depth.hu/).

## Insight
You should be able to see in your browser something like this:
![screen1](traverse-depth-hu-1.png "sscreen1")
![screen1](traverse-depth-hu-2.png "sscreen1")

## Subjects
Currently processed are the followings: 

Artificial Intelligence,  Computation and Language,  Computational Complexity,  Computational Engineering, Finance, and Science,  Computational Geometry,  Computer Science and Game Theory,  Computer Vision and Pattern Recognition,  Computers and Society,  Cryptography and Security,  Data Structures and Algorithms,  Databases,  Digital Libraries,  Discrete Mathematics,  Distributed, Parallel, and Cluster Computing,  Emerging Technologies,  Formal Languages and Automata Theory,  General Literature,  Graphics,  Hardware Architecture,  Human-Computer Interaction,  Information Retrieval,  Information Theory,  Logic in Computer Science,  Machine Learning,  Mathematical Software,  Multiagent Systems,  Multimedia,  Networking and Internet Architecture,  Neural and Evolutionary Computing,  Numerical Analysis,  Operating Systems,  Other Computer Science,  Performance,  Programming Languages,  Robotics,  Social and Information Networks,  Software Engineering,  Sound,  Symbolic Computation,  Systems and Control

(C) Copyright Béky Miklós, All rights reserved.