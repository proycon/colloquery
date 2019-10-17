.. image:: http://applejack.science.ru.nl/lamabadge.php/colloquery
   :target: http://applejack.science.ru.nl/languagemachines/

.. image:: https://www.repostatus.org/badges/latest/inactive.svg
   :alt: Project Status: Inactive – The project has reached a stable, usable state but is no longer being actively developed; support/maintenance will be provided as time allows.
   :target: https://www.repostatus.org/#inactive

Colloquery
============

Colloquery is a web application to search for phrase translations, or
collocations, as well as synonyms,in bilingual phrase translation tables.

It is developed for `Van Dale <http://vandale.nl>`_ by the `Centre for Language
and Speech Technology <http://www.ru.nl/clst>`_, Radboud University Nijmegen, and is licensed under the
Affero GNU Public License.

.. image:: https://raw.github.com/proycon/colloquery/master/screenshot.jpg
    :alt: Colloquery screenshot
    :align: center

Installation
--------------

First, clone this repository and edit ``settings.py``.

Colloquery is not trivial to set-up and train, as it relies on numerous
external dependencies:

* Python 3
* `MongoDB <https://mongodb.com>`_
* `mongoengine <http://mongoengine.org>`_
* `Django <https://djangoproject.com>`_

On Debian/Ubuntu systems, these can be installed using ``sudo apt-get install
python3 mongodb python3-mongoengine python3-django``.

For the data generation step, the following additional dependencies are required:

* `colibri-core <https://proycon.github.io/colibri-core>`_ (shipped as part of
  `LaMachine <https://proycon.github.io/LaMachine>`_)
* `colibri-mt <https://github.com/proycon/colibri-mt>`_

To create phrase translation-tables in the first place, use the Moses training
pipeline, which in turn invokes GIZA++:

* `Moses <http://statmt.org/moses/>`_
* `GIZA++ <https://github.com/moses-smt/giza-pp>`_

Data Generation
--------------------

* Prepare your parallel corpus files. A parallel corpus consists of two plain-text UTF8 encoded
  files, one for the source language (``corpus.fr`` in our example) and one for the target
  language (``corpus.en``).  Make sure they are tokenised, lower-cased and
  contain one sentence per line (you can use `ucto
  <https://languagemachines.github.io/ucto>`_ for this), sentences on the same line in the other file
  are considering translations.
* Train a phrase translation table using Moses::

  $ /path/to/moses/scripts/training/train-model.perl -external-bin-dir /path/to/moses/bin -root-dir .  --parallel --corpus corpus --f fr --e en  --first-step 1 --last-step 8

* Invoke the data generation pipeline of Colloquery, adjust the thresholds as
  needed (see ``./manage.py generatedata --help``). This assumes a running
  and properly configured MongoDB::

  ./manage.py generatedata --title "YourCorpus" --phrasetable corpus.fr-en.phrasetable --sourcelang fr --targetlang en --targetcorpus corpus.fr --sourcecorpus corpus.en --pst 0.2 --pts 0.2 --divergencethreshold 0.1 --freqthreshold 4

The Moses and data generation pipeline may take considerable time and system
resources (most notably memory). Set sane thresholds to prevent the data from
becoming unmanageably large.

