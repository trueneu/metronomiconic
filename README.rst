Metronomiconic
==============

Metronome which does all you'd expect from a metronome, and has a unique
double/half tempo feature! An iconic metronome.

Installation
------------

``pip install metronomiconic``

It requires python3+ to run.

Do you know Victor Wooten?
--------------------------

In one of his videos on working with metronome, this incredible musician
showed an exercise to build one's rhythm feel: you play a groove/a
phrase to a comfortable click tempo, say 120 bpm. Then, when you feel
you're in the pocket, you drop the tempo 2 times, but play the same. You
just end up with less clicks to hear. When you're confident you've
caught the pulse, you drop it once again. In the end, you're playing the
same fast groove in 120 bpm, supported by only 1 click per 2 or even 4
bars. Isn't that an incredible exercise?

But here's the problem: when practicing, you need to stop and adjust
your metronome tempo carefully for a few seconds, effectively losing the
pocket and feel. With ``metronomiconic`` it only takes one keypress.

Please read further.

Usage
-----

Install it.

Create a directory under your home directory called ``.metronomiconic``.
Place there two or three sound files (``bar.wav``, ``beat.wav``,
``division.wav`` which can be omitted, and if it is, you will be unable
to hear subdivision notes).

A collection of default click sounds from popular DAWs can be found
`here <https://dl.dropboxusercontent.com/u/1053122/metronome%20samples.zip>`__.
The reason I do not include them in distribution in simple: they are not
free, and the free ones I've heard... well I don't like them.

You're ready to go. Type ``metronomic`` in your favorite terminal
emulator.

Press space bar to stop or start. Use arrow keys and arrow keys with
shift to change tempo. Use digits, alt+up and alt+down to change time
signature (1 to 9 for beat count and 1,2,4,8,16 for beat length are
supported). Tempo is measured with quarter notes.

Press p to stop/start play subdivisions. Press t, q or s to switch
triplet, quintuplet or septuplet subdivision mode starting with the next
bar (normally, every beat is subdivisioned in sixteenth notes).

And now for the most cool part: doubling and halfing the tempo.

Press u or d to double or half the tempo from the next bar.

Notes
-----

I'm a learning bass player, and I couldn't get why I can't find a
metronome that would do this half/double thing for me, so I had to come
up with my own. The 'learning functions', as I call them, that include
half/double and tri-, quintu- and septuplet modes work from the next bar
played. All the other changes take place immediately.

I've tested metronome's accuracy for a little while, but so far I can
say it's pretty accurate, compared with a few hardware, DAW and online
metronomes.

Do not look in the code! It's very messy and unmaintainable, and there
is at least one very dirty hack.

Released under MIT license.
