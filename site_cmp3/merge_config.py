import os, yaml, pprint
from rucio.client.rseclient import RSEClient

class MergedCEConfiguration(object):

    CONFIG_PREFIX = "CE_config."
    """
            Enable/disable CE for the site
            Thresholds for CE actions (fraction of dark/missing files to abort the action)
            List of roots to scan
            List of ignored directories
            Scanning concurrency
            Scanning timeout
            Server address
    """

    def __init__(self, rse, config_file, account="root"):
        self.RSEClient = RSEClient(account=account)
        self.RSE = rse
        self.ConfigFromFile = yaml.load(open(config_file, "r"), Loader=yaml.SafeLoader)
        self.ConfigFromRSE = self.config_from_rse()

    def config_from_rse(self):
        rse_config = self.RSEClient.list_rse_attributes(rse)
        cfg = {}
        if self.CONFIG_PREFIX+"disabled" in rse_config:     
            cfg["disabled"] = rse_config[self.CONFIG_PREFIX+"disabled"] == "yes"
        if self.CONFIG_PREFIX+"ignore_list" in rse_config: 
            cfg["ignore_list"] = rse_config[self.CONFIG_PREFIX+"ignore_list"].split(",")

        scanner_cfg = {}
        if self.CONFIG_PREFIX+"server" in rse_config:          
            scanner_cfg["server"] = rse_config[self.CONFIG_PREFIX+"server"]
        if self.CONFIG_PREFIX+"server_root" in rse_config:     
            scanner_cfg["server_root"] = rse_config[self.CONFIG_PREFIX+"server_root"]
        if self.CONFIG_PREFIX+"roots" in rse_config:           
            scanner_cfg["roots"] = [{"path":path} for path in rse_config[self.CONFIG_PREFIX+"roots"].split(",")]
        if self.CONFIG_PREFIX+"nworkers" in rse_config:        
            scanner_cfg["nworkers"] = int(rse_config[self.CONFIG_PREFIX+"nworkers"])
        if self.CONFIG_PREFIX+"timeout" in rse_config:         
            scanner_cfg["timeout"] = int(rse_config[self.CONFIG_PREFIX+"timeout"])
        cfg["scanner"] = scanner_cfg

        if self.CONFIG_PREFIX+"max_dark_fraction" in rse_config:       
            cfg["dark_action"] = {"max_fraction":float(rse_config[self.CONFIG_PREFIX+"max_dark_fraction"])}
        if self.CONFIG_PREFIX+"max_missing_fraction" in rse_config:    
            cfg["missing_action"] = {"max_fraction":float(rse_config[self.CONFIG_PREFIX+"max_missing_fraction"])}
        return cfg

    def merge(self, defaults, overrides):
        out = defaults.copy()
        for key, value in overrides.items():
            if isinstance(value, dict):
                out[key] = self.merge(defaults.get(key, {}), value)
            else:
                out[key] = value
        return out

    def config(self):
        rse_config = self.merge(self.ConfigFromFile["rses"].get("*", {}), self.ConfigFromFile["rses"].get(rse, {}))
        #print("merged rse config from file:")
        #pprint.pprint(rse_config)
        out = self.merge(rse_config, self.ConfigFromRSE)
        #print("final merged:", out)
        return out

if __name__ == "__main__":
    import sys, getopt
    opts, args = getopt.getopt(sys.argv[1:], "")
    opts = dict(opts)
    
    cmd = args[0]
    if cmd == "merge":
        rse, config_file = args[1:]
        cfg = MergedCEConfiguration(rse, config_file)
        yaml.dump(cfg.config(), sys.stdout)
    elif cmd == "get":
        merged_config_file, path = args[1:]
        cfg = yaml.load(open(merged_config_file, "r"), Loader=yaml.SafeLoader)
        path = path.split(".")
        try:
            while path:
                cfg = cfg.get(path[0])
                path.pop(0)
        except KeyError:
            sys.exit(1)
        print(cfg)
        
        
    

