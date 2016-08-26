options:
    # todo(obaranov) This is deprecated option. Use --inventory flag from the subcommand spec
    inventory:
        help: Inventory file
        type: str
    mirror:
        type: Value
        help: |
            Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
            (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)
        default: ''
