import argparse, ast, hashlib, json, math, multiprocessing, os
import platform, re, requests, shutil, subprocess, sys, time, zipfile

timecontrol = "1000.0"
GAMES_PER_CONCURRENCY = 16 
concurrency = GAMES_PER_CONCURRENCY 
SAVE_PGN_FILES = False
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() != 'Darwin' and platform.system() != 'Windows'

def killCutechess(cutechess):
    try:
        cutechess.kill()
        cutechess.wait()
        cutechess.stdout.close()
    except KeyboardInterrupt: sys.exit()
    except Exception as error: pass

def getCutechessCommand():

    # General Cutechess options
    generalflags = '-repeat -recover -srand {0} -resign {1} -draw {2}'.format(
        int(time.time()), 'movecount=3 score=400', 'movenumber=40 movecount=8 score=10'
    )

    # Options about tournament conditions
    setupflags = '-concurrency {0} -games {1}'.format(
        concurrency, concurrency * GAMES_PER_CONCURRENCY
    )

    # Options for the Dev Engine
    # devflags = '-engine dir=Versions/ cmd=./{0} proto={1} tc={2}{3} name={4}'.format(
    devflags = '-engine cmd=./Engines/{0} proto=uci tc={1}'.format(
        sys.argv[1],
        timecontrol
    )

    # Options for the Base Engine
    baseflags = '-engine cmd=./Engines/{0} proto=uci tc={1}'.format(
        sys.argv[2],
        timecontrol
    )

    # # Options for opening selection
    bookflags = ""
    # bookflags = '-openings file=Books/{0} format={1} order=random plies=16'.format(
    #     data['test']['book']['name'], data['test']['book']['name'].split('.')[-1]
    # )

    # Save PGN files if requested, as Engine-Dev_vs_Engine-Base
    if SAVE_PGN_FILES:
       bookflags += ' -pgnout PGNs/{0}_vs_{1}'.format(sys.argv[1], sys.argv[2])

    # Combine all flags and add the cutechess program callout
    options = ' '.join([generalflags, setupflags, devflags, baseflags, bookflags])
    if IS_LINUX:
        return './cutechess-linux {0}'.format(options), concurrency
    elif IS_MACOS:
        return './cutechess {0}'.format(options), concurrency
    else:
        print("EasyBench only runs in MacOS and Linux")
        return ""

def processCutechess(cutechess, concurrency):

    # Tracking for game results
    crashes = timelosses = 0
    test_crashes = base_crashes = 0
    score = [0, 0, 0]; sent = [0, 0, 0]
    errors = ['on time', 'disconnects', 'connection stalls', 'illegal']

    while True:

        # Output the next line or quit when the pipe closes
        line = cutechess.stdout.readline().strip().decode('ascii')
        if line != '': print(line)
        else: cutechess.wait(); return

        # Updated timeloss/crash counters
        timelosses += 'on time' in line

        if 'White disconnects' in line:
            if 'Dratini vs' in line: # Base was playing white 
                base_crashes += 1
            else:
                test_crashes += 1
        elif 'Black disconnects' in line:
            if 'Dratini vs' in line: # Base was playing white 
                test_crashes += 1
            else:
                base_crashes += 1
        
        # Report any engine errors to the server
        for error in errors:
            if error in line:
                print(error)

        # Parse updates to scores
        if line.startswith('Score of'):

            # Format: Score of test vs base: W - L - D  [0.XXX] N
            score = list(map(int, line.split(':')[1].split()[0:5:2]))
            score[0] -= base_crashes
            score[1] -= test_crashes
            print(score)

    print(score)


def main():
    command, concurrency = getCutechessCommand()
    print("Launching Cutechess\n{0}\n".format(command))

    cutechess = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    processCutechess(cutechess, concurrency)

if __name__ == "__main__":
    main()

