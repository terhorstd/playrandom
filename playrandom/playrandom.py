#!/usr/bin/env python
#
# find all mplayer files and play a random one
#
'''
Usage:
    playrandom [options] [<directory>...]

Options:
    --dark              set additional flags for playing movies in a dark environment
    --fs                start videos fullscreen
    -V, --volume=<x>    set initial volume to <x> percent [default: 80]
    -v, --verbose       print more stuff
    -s, --volstep=<x>   volume step [default: 3]
    -h, --help          display this help text

'''
import sys, os
import subprocess, shlex
import docopt
import random
import time
import logging
from pprint import pformat

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)

try:
    import color
except ImportError:
    class FakeColor(object):
        @classmethod
        def __getattr__(cls, arg):
            return lambda x:x
    color = FakeColor()


class MplayerWrapper(object):
    def __init__(self, volume=None, volstep=None, dark=False, jack=False, fs=False):

        self.post_play_hooks = []
        self.pre_play_hooks = []

        # mplayer stuff
        cmd = shlex.split("mplayer -softvol")
        if fs:
            cmd.extend(['-fs'])
        if jack:
            cmd.extend("-ao jack".split())
        else:
            cmd.extend("-ao pulse".split())
        if volume is not None:
            cmd.extend(("-volume %d" % int(volume)).split())
        if volstep is not None:
            cmd.extend(("-volstep %d" % int(volstep)).split())
        if dark:
            cmd.extend(shlex.split("-vo gl -brightness -40 -contrast -10"))
        self.mplayer_cmd = cmd
        log.debug("using mplayer command: %s", cmd)

    def PlayAVfile(self, fname):
        # play with mplayer
        if not os.path.isfile(fname):
            raise RuntimeError("'%s' is not a file" % fname)
        fname.replace("'", "\\'")
        log.info(color.green("*** playing '%s'" % fname))
        cmd = self.mplayer_cmd.copy()    # copy list
        cmd.append(fname)

        # pre-play hooks
        for hook in self.pre_play_hooks:
            hook(fname)

        log.debug("calling %s", cmd)
        p = subprocess.Popen(cmd)
        try:
            p.wait()
            log.info("subprocess finished.")
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt: terminating %s subprocess...", cmd[0])
            try:
                p.terminate()
            except OSError:
                pass
            p.wait()
            log.info("subprocess was terminated.")
            raise   # re-raise the interrupt

        # post-play hooks
        for hook in self.post_play_hooks:
            hook(fname)


class FileSelector(object):
    class Recentlist(list):
        def __init__(self):
            super(FileSelector.Recentlist, self).__init__()
            self.filename = None
            self._load_from_file()  # try loading
            self.super = super(FileSelector.Recentlist, self)

        def _load_from_file(self, filename='.playrandoms'):
            self.clear()
            try:
                with open(filename, 'r') as recent:
                    for line in recent:
                        playedtime, playedfile = line.strip().split(" ",1)
                        self.super.append(playedfile)
                log.info("loaded recentlist with %d entries.", len(self))
                self.filename = filename
            except FileNotFoundError as e:
                log.debug("no recentlist found.")
                pass
            except Exception as e:
                log.warning("could not load %s. recentlist empty.", filename)
                pass

        def append(self, entry):
            if self.filename is not None:
                with open(self.filename, 'a') as out:
                    out.write("%d %s\n" % (time.time(), entry))
            self.super.append(entry)

        def set_filename(self, filename):
            self.filename = filename

    def __init__(self, dirs):
        self.dirs = dirs
        self.recentlist = self.Recentlist()    # list of recently played files
        self.files = list()         # list of found files
        self.first_find = True      # flag for find verbosity
        self.pick = self.__newestpick   # default pick algorithm

        if "Videos" in os.getcwd():
            self.recentlist.set_filename('.playrandoms')

        logging.info("searching...\n\t%s" % ("\n\t".join(self.dirs)))

    def __build_find_cmd(self):
        # create a find command expression
        audio_ext = ['mp3', 'ogg', 'wma']
        video_ext = ['mpg', 'mpeg', 'avi', 'mov', 'm4v', 'mp4', 'wmv', 'flv', 'mkv']
        audio = "\( %s \)" % " -o ".join(["-iname '*.%s'" % ext for ext in audio_ext])
        video = "\( %s \)" % " -o ".join(["-iname '*.%s'" % ext for ext in video_ext])
        if self.first_find:
            log.info("audio extensions: %s" % color.bold(str(audio_ext)))
            log.info("video extensions: %s" % color.bold(str(video_ext)))
        video = "\( %s -and -size +5M -not -iwholename '*sample*' \)" % video

        findstring = "-type f -and \( %s -or %s \)" % (video, audio)

        find_cmd = "/usr/bin/find -L '%(where)s' %(find)s" % {'where':"' '".join(self.dirs), 'find':findstring}
        if self.first_find:
            log.debug(color.gray(find_cmd))
            self.first_find = False
        return find_cmd

    def refresh(self):
        '''
        refresh the list of available files by scanning the filesystem
        '''
        # old functionality to play a playlist file. has to be moved out
        #if os.path.isfile(self.dirs[0]):
        #    files = open(self.dirs[0]).read().strip().split("\n")
        #    return files

        find_cmd = self.__build_find_cmd()

        text = None
        try:
            log.debug("running %s", shlex.split(find_cmd))
            text = subprocess.check_output(shlex.split(find_cmd)).decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            log.error(e)
            text = e.output.decode('utf-8').strip()

        self.files = []
        if len(text) > 0:
            self.files = text.split('\n')
        assert len(self.files) > 0, "no suitable files found!"

    def __randompick(self):
        '''
        returns one arbitrary entry from the current list of files

        >>> x = FileSelector()
        >>> x.__randompick()
        '''
        log.info("*** choosing randomly from %d files (%d played = %4.1f%%)", len(self.files), len(self.recentlist), 100.*len(self.recentlist)/len(self.files))
        tries = 0
        maxtries = 10
        notplayed = [x for x in self.files if not x in self.recentlist]
        if len(notplayed) == 0:
            log.info(color.yellow("played all %d items in list. clearing recentlist to start over again."), len(self.files))
            self.recentlist.clear()
            notplayed = self.files
        return random.choice(notplayed) # choose one

    def __newestpick(self):
        '''
        returns the newest file in the current list of files that was not played before.
        '''
        log.info("*** choosing latest from %d files (%d played = %4.1f%%)", len(self.files), len(self.recentlist), 100.*len(self.recentlist)/len(self.files))

        def fage(filename):
            try:
                sr = os.stat(filename)
                return time.time() - sr.st_ctime
            except OSError as e:
                return 999999999

        unplayed = [f for f in self.files if not f in self.recentlist]
        if len(unplayed) < 1:
            log.warning(color.magenta("no file found that is not in the recentlist! shifting out oldest entries..."))
            assert len(self.recentlist) > 0, "can not remove entries from empty recentlist"
            self.recentlist = self.recentlist[max(len(self.recentlist)/10, 1):]
            unplayed = [f for f in self.files if not f in self.recentlist]

        latest_file = sorted(unplayed, key=fage)[0]
        age = fage(latest_file)

        log.debug("latest file is %s (age %d sec)", latest_file, age)

        if age > 600:    # switch to random mode if newest file is older than 10 min
            log.info(color.magenta("newest file is %d sec old. switching to random mode." % age))
            self.pick = self.__randompick
            return self.pick()

        return latest_file

def main():
    args = docopt.docopt(__doc__)
    if args["--verbose"]:
         log.setLevel(logging.DEBUG)
    log.debug(pformat(args))

    mplayer = MplayerWrapper(
        volume = args['--volume'],
        volstep = args['--volstep'],
        dark = args['--dark'],
        fs = args['--fs'],
    )

    selector = FileSelector(args.get('<directory>', [os.curdir,]))

    mplayer.post_play_hooks.append(selector.recentlist.append)

    while True:
        selector.refresh()
        fname = selector.pick()

        try:
            mplayer.PlayAVfile(fname)
        except KeyboardInterrupt:
            break

    # exit steps
    #time.sleep(1) # stay available for mplayer child to terminate gracefully
    log.info("exit")



if __name__ == '__main__':
    main()
