# Why?

I see [people](https://community.ui.com/questions/How-do-I-test-my-config-gateway-json-file/b477ab84-6db5-425e-ab73-70391896bee9), and even [the official Ubiquiti doc](https://help.ui.com/hc/en-us/articles/215458888-UniFi-USG-Advanced-Configuration-Using-config-gateway-json) telling others to validate their `config.gateway.json` file with something as simple as `python -m json.tool config.gateway.json`. The problem with this is that it _simply_ checks for JSON syntax, not for the content itself. On the opposite side, a JSON schema allows you to check the _content_ of your JSON and decreases your chances of submitting a buggy config that will result in a provision loop.

# Get it

You can get the schema I generated from my hardware/version (see **Issues** below) [here](schemas/schema.usg-3p.4.4.56.yaml).

# DIY

Grab the config files from your gateway and run the script:
```shell
scp -r admin@your-router.example.com:/opt/vyatta/share/vyatta-cfg/templates/ .
./builder.py templates unifi.schema.yaml
```

For readability, the output file is in YAML. Jetbrains IDEs can still use them as schema sources. If your tool/IDE can not, converting YAML to JSON is trivial.

# Issues

I developed this script based on the following hardware. I have no idea if different models have different options. Please be cautious and report it if your hardware has a different schema.

```
$ show version 
Version:      v4.4.56
Build ID:     5449062
Build on:     10/20/21 08:31
Copyright:    2012-2020 Ubiquiti, Inc.
HW model:     UniFi-Gateway-3
```

If you find issues with the script or the generated schema file, please open an issue and attach:
- The generated schema (it does NOT contain any info on your gateway/network)
- The output of `show version`
- The (redacted) part of your JSON file or output of `mca-ctrl -t dump-cfg`
