subparsers:
    jenkins:
        formatter_class: RawTextHelpFormatter
        help: Infrared integration with the jenkins ci
        options:
            config:
                type: IniFile
                help: the jenkins configuration and authentication info
                required: yes
            from-file:
                type: IniFile
                help: The file with the job parameters
                required: yes
