####################################################
# Colloquery
#   by Maarten van Gompel
#   Centre for Language and Speech Technology
#   Radboud University Nijmegen
#
#  developed for Van Dale
#
#  https://github.com/proycon/colloquery
#  Licensed under AGPLv3
###################################################

import mongoengine

class Collection(mongoengine.Document):
    name = mongoengine.StringField()
    sourcelanguage = mongoengine.StringField()
    targetlanguage = mongoengine.StringField()
    meta = {
        'indexes': [ 'name' ]
    }


class Collocation(mongoengine.Document):
    collection = mongoengine.ReferenceField(Collection)
    language = mongoengine.StringField(max_length=3)
    text = mongoengine.StringField(max_length=125)
    freq = mongoengine.IntField() #occurrence frequency (absolute)

    meta = {
        'indexes': [
            {
                'fields': ['$text'],
            },
            {
                'fields': ('collection', 'language', 'text'),
                'unique': True,
            }
        ]
    }

class Translation(mongoengine.Document):
    source = mongoengine.ReferenceField(Collocation)
    target = mongoengine.ReferenceField(Collocation)
    prob = mongoengine.FloatField() #p(target|source)
    revprob = mongoengine.FloatField() #p(source|target)

    meta = {
        'indexes': [
            'source',
            'target',
        ]
    }

stopwords = {
'en': set(x for x in """
i
me
my
myself
we
our
ours
ourselves
you
your
yours
yourself
yourselves
he
him
his
himself
she
her
hers
herself
it
its
itself
they
them
their
theirs
themselves
what
which
who
whom
this
that
these
those
am
is
are
was
were
be
been
being
have
has
had
having
do
does
did
doing
a
an
the
and
but
if
or
because
as
until
while
of
at
by
for
with
about
against
between
into
through
during
before
after
above
below
to
from
up
down
in
out
on
off
over
under
again
further
then
once
here
there
when
where
why
how
all
any
both
each
few
more
most
other
some
such
no
nor
not
only
own
same
so
than
too
very
's
't
can
will
just
don
should
now
'd
'll
'm
're
've
n't
ain
aren
couldn
didn
doesn
hadn
hasn
haven
isn
ma
mightn
mustn
needn
shan
shouldn
wasn
weren
won
wouldn
""".split('\n') if x),
'nl': set(x for x in """
de
en
van
ik
te
dat
die
in
een
hij
het
niet
zijn
is
was
op
aan
met
als
voor
had
er
maar
om
hem
dan
zou
of
wat
mijn
men
dit
zo
door
over
ze
zich
bij
ook
tot
je
mij
uit
der
daar
haar
naar
heb
hoe
heeft
hebben
deze
u
want
nog
zal
me
zij
nu
ge
geen
omdat
ietshttps://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip
worden
toch
al
waren
veel
meer
doen
toen
moet
ben
zonder
kan
hun
dus
alles
onder
ja
eens
hier
wie
werd
altijd
doch
wordt
wezen
kunnen
ons
zelf
tegen
na
reeds
wil
kon
niets
uw
iemand
geweest
andere
""".split('\n') if x)
}


