import soundfile
import pysoundcard
import time
import threading
import timeit
import warnings
import urwid
import os
import sys

warnings.filterwarnings("ignore")  # this is a dirty, very dirty hack to avoid Buffer Underflow messages

class ClickTimerThread(threading.Thread):
    tempo = 60
    beats_in_bar = 4
    new_beats_in_bar = 4
    reread_time_sig_flag = False
    divisions_in_beats = 4
    new_divisions_in_beats = 4
    time_sig_bottom = 4
    new_time_sig_bottom = 8
    is_playing = False
    _precision = 1000  # milliseconds
    _sleep_time = 0.001  # seconds

    _play_beats = True
    _play_divisions = True

    def __init__(self, stop_event, reload_event, start_event, exit_event,
                 bar_file, beat_file, division_file):
        threading.Thread.__init__(self)
        self._stop_event = stop_event
        self._reload_event = reload_event
        self._start_event = start_event
        self._exit_event = exit_event
        self._bar_interval = 0
        self._beat_interval = 0
        self._division_interval = 0
        self._divisions_in_bar = 0

        self._bar_file = bar_file
        self._beat_file = beat_file
        self._division_file = division_file

        self._old_tick = -1
        self._current_tick = 0
        self._first_bar = True
        self._start_clock = None

        self._reload_all()
        self._pysoundcard_stream = pysoundcard.Stream(self._bar_audio_fs, blocksize=128, latency=0)
        self._pysoundcard_stream.start()

    def reload_all(self):
        self._reload_all()

    def _reload_tempo(self):
        if self.reread_time_sig_flag:
            self.reread_time_sig_flag = False
            self.beats_in_bar = self.new_beats_in_bar
            self.divisions_in_beats = self.new_divisions_in_beats
            self.time_sig_bottom = self.new_time_sig_bottom

        self._calculate_intervals()
        self._calculate_divisions_in_bar()

        self._current_tick = 0
        self._old_tick = -1
        self._first_bar = True

        self._start_clock = int(timeit.default_timer() * self._precision)

    def reload_tempo(self):
        self._reload_tempo()

    def _reload_all(self):
        self._reload_tempo()
        self._load_sounds()

    def _load_sounds(self):
        self._bar_audio_data, self._bar_audio_fs = soundfile.read(self._bar_file)
        self._beat_audio_data, self._beat_audio_fs = soundfile.read(self._beat_file)
        if self._division_file:
            self._division_audio_data, self._division_audio_fs = soundfile.read(self._division_file)
        else:
            self._division_audio_data, self._division_audio_fs = None, None

    def _calculate_intervals(self):
        beat_interval = 60 / self.tempo * 4 / self.time_sig_bottom * self._precision
        division_interval = beat_interval / self.divisions_in_beats
        bar_interval = beat_interval * self.beats_in_bar

        #beat_interval = 60 / self.tempo / self.divisions_in_beats * 4 * self._precision
        #bar_interval = beat_interval * self.beats_in_bar
        #division_interval = beat_interval // self.divisions_in_beats

        #print(bar_interval)
        #print(beat_interval)
        #print(division_interval)

        #print(self.divisions_in_beats)
        #print(self.time_sig_bottom)

        self._bar_interval = bar_interval
        self._beat_interval = beat_interval
        self._division_interval = division_interval

    def _calculate_divisions_in_bar(self):
        self._divisions_in_bar = self.beats_in_bar * self.divisions_in_beats

    def run(self):
        self.is_playing = True
        self._start_clock = int(timeit.default_timer() * self._precision)
        while True:
            if self._stop_event.is_set():
                self._stop_event.clear()
                self.is_playing = False
                while True:
                    if self._exit_event.is_set():
                        break
                    if self._start_event.is_set():
                        self.is_playing = True
                        self._start_clock = int(timeit.default_timer() * self._precision)
                        self._start_event.clear()
                        break
                    time.sleep(self._sleep_time)
            if self._exit_event.is_set():
                break
            curr_clock = int(timeit.default_timer() * self._precision)
            clocks_diff = curr_clock - self._start_clock
            self._current_tick = int(clocks_diff // self._division_interval)
            if self._current_tick > self._old_tick:
                if self._first_bar:  # first click jitter elimination hack
                    self._first_bar = False

                if self._current_tick % self._divisions_in_bar == 0:
                    self._pysoundcard_stream.write(self._bar_audio_data)
                    if self._reload_event.is_set():
                        self._reload_tempo()
                        self._reload_event.clear()
                elif self._play_beats and self._current_tick % self.divisions_in_beats == 0:
                    self._pysoundcard_stream.write(self._beat_audio_data)
                elif self._play_divisions:
                    if self._division_audio_fs:
                        self._pysoundcard_stream.write(self._division_audio_data)
                self._old_tick = self._current_tick
            time.sleep(self._sleep_time)
        self._pysoundcard_stream.stop()


class Metronomiconic(object):
    #_version = version.__version__
    _version = "0.0.2"

    _help_message = """
Metronomiconic {v}

Use arrows up and down to change tempo by 1
left and right by 4
shift+up/down by 10
shift+left/right by 20
space to stop/start
d and u to Drop or raise (u) tempo 2 times
digits to set time signature to digit/x
meta+up/down to set time signature to x/[1,2,4,8,16]

p to switch divisions Playing
t to switch Triplet mode
q to switch Quintuplet mode
s to switch Septuplet mode

Before changing time signature, quit triplet/quintuplet/seventuplet modes first.

esc to Quit.

""".format(v=_version)

    def _time_sig(self):
        if self._play_thread.reread_time_sig_flag:
            return "\nTime sig: {sig}/{sig2}\n".format(sig=int(self._play_thread.new_beats_in_bar),
                                                       sig2=int(self._play_thread.new_time_sig_bottom))
        else:
            return "\nTime sig: {sig}/{sig2}\n".format(sig=int(self._play_thread.beats_in_bar),
                                                       sig2=int(self._play_thread.time_sig_bottom))

    def _triplet_message(self):
        if self._triplet_mode:
            return "\nTriplet mode ON"
        elif self._quantuplet_mode:
            return "\nQuantuplet mode ON"
        elif self._seventuplet_mode:
            return "\nSeptuplet mode ON"
        else:
            return ""

    def _urwid_tempo_text(self):
        return urwid.Text("{help}{sig}Tempo: {tempo} bpm\n{triplet}".format(
            tempo=self._play_thread.tempo, help=self._help_message, triplet=self._triplet_message(),
            sig=self._time_sig())
        )

    def _urwid_widget(self):
        return urwid.Filler(self._urwid_tempo_text(), 'top')

    def __init__(self):
        bar_file = os.path.expanduser("~/.metronomiconic/bar.wav")
        beat_file = os.path.expanduser("~/.metronomiconic/beat.wav")
        division_file = os.path.expanduser("~/.metronomiconic/division.wav")

        if not os.path.exists(bar_file) or not os.path.exists(beat_file):
            print("{bar} and/or {beat} files not found. Please put them there. You can also use aiff files, just"
                  " make sure their extensions are '.wav'".format(bar=bar_file, beat=beat_file))
            sys.exit(2)
        if not os.path.exists(division_file):
            division_file = None

        self._stop_event = threading.Event()
        self._reload_event = threading.Event()
        self._start_event = threading.Event()
        self._exit_event = threading.Event()
        self._stop_event.set()
        self._play_thread = ClickTimerThread(self._stop_event, self._reload_event, self._start_event, self._exit_event,
                                             bar_file, beat_file, division_file)
        self._play_thread.start()
        self._play_thread.tempo = 60
        self._triplet_mode = False
        self._quantuplet_mode = False
        self._seventuplet_mode = False

        self._loop = urwid.MainLoop(self._urwid_widget(), unhandled_input=self.user_input_handler)

    def _play_thread_stop(self):
        self._exit_event.set()
        self._play_thread.join()
        self._play_thread = None

    def _urwid_redraw(self):
        self._loop.widget = self._urwid_widget()
        self._loop.draw_screen()

    def user_input_handler(self, key):
        if key in ['esc']:
            if self._play_thread:
                self._play_thread_stop()
            raise urwid.ExitMainLoop()
        elif key in [' ']:
            if not self._play_thread.is_playing:
                self._play_thread.reload_all()
                self._start_event.set()
            else:
                self._stop_event.set()
        elif key in ['up']:
            self._play_thread.tempo += 1
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['down']:
            self._play_thread.tempo -= 1
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['left']:
            self._play_thread.tempo -= 4
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['right']:
            self._play_thread.tempo += 4
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['d']:
            self._play_thread.tempo /= 2
            self._reload_event.set()
            self._urwid_redraw()
        elif key in ['u']:
            self._play_thread.tempo *= 2
            self._reload_event.set()
            self._urwid_redraw()
        elif key in ['shift up']:
            self._play_thread.tempo += 10
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['shift down']:
            self._play_thread.tempo -= 10
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['shift left']:
            self._play_thread.tempo -= 20
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['shift right']:
            self._play_thread.tempo += 20
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if self._triplet_mode or self._seventuplet_mode or self._quantuplet_mode:
                return
            self._play_thread.beats_in_bar = int(key)
            self._play_thread.reload_tempo()
            self._urwid_redraw()
        elif key in ['p']:
            self._play_thread._play_divisions = not self._play_thread._play_divisions
        elif key in ['t']:
            if self._quantuplet_mode or self._seventuplet_mode:
                return
            self._triplet_mode = not self._triplet_mode
            if self._triplet_mode:
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * 3/(16 / self._play_thread.time_sig_bottom)
            else:
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * (16 / self._play_thread.time_sig_bottom)/3
            self._play_thread.new_beats_in_bar = self._play_thread.beats_in_bar
            self._play_thread.new_time_sig_bottom = self._play_thread.time_sig_bottom
            self._play_thread.reread_time_sig_flag = True
            self._reload_event.set()
            self._urwid_redraw()
        elif key in ['q']:
            if self._triplet_mode or self._seventuplet_mode:
                return
            self._quantuplet_mode = not self._quantuplet_mode
            if self._quantuplet_mode:
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * 5/(16 / self._play_thread.time_sig_bottom)
            else:
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * (16 / self._play_thread.time_sig_bottom)/5
            self._play_thread.new_beats_in_bar = self._play_thread.beats_in_bar
            self._play_thread.new_time_sig_bottom = self._play_thread.time_sig_bottom
            self._play_thread.reread_time_sig_flag = True
            self._reload_event.set()
            self._urwid_redraw()
        elif key in ['s']:
            if self._triplet_mode or self._quantuplet_mode:
                return
            self._seventuplet_mode = not self._seventuplet_mode
            if self._seventuplet_mode:
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * 7/(16 / self._play_thread.time_sig_bottom)
            else:
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * (16 / self._play_thread.time_sig_bottom)/7
            self._play_thread.new_beats_in_bar = self._play_thread.beats_in_bar
            self._play_thread.new_time_sig_bottom = self._play_thread.time_sig_bottom
            self._play_thread.reread_time_sig_flag = True
            self._reload_event.set()
            self._urwid_redraw()
        elif key in ['meta up']:
            if self._triplet_mode or self._seventuplet_mode or self._quantuplet_mode:
                return
            if self._play_thread.time_sig_bottom < 16:
                self._play_thread.new_beats_in_bar = self._play_thread.beats_in_bar
                self._play_thread.new_time_sig_bottom = self._play_thread.time_sig_bottom * 2
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats / 2
                self._play_thread.reread_time_sig_flag = True
                self._play_thread.reload_tempo()
                self._urwid_redraw()
        elif key in ['meta down']:
            if self._triplet_mode or self._seventuplet_mode or self._quantuplet_mode:
                return
            if self._play_thread.time_sig_bottom > 1:
                self._play_thread.new_beats_in_bar = self._play_thread.beats_in_bar
                self._play_thread.new_time_sig_bottom = self._play_thread.time_sig_bottom / 2
                self._play_thread.new_divisions_in_beats = self._play_thread.divisions_in_beats * 2
                self._play_thread.reread_time_sig_flag = True
                self._play_thread.reload_tempo()
                self._urwid_redraw()
        #else:
        #    print(key)

    def run(self):
        self._loop.run()


