import docopt

from kaniko import main


def __main__(argv=None):
    main.main(docopt.docopt(main.__doc__, argv=argv, options_first=True))


if __name__ == "__main__":
    __main__()
