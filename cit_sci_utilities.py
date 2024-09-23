import os, datetime, shutil 

def remove_items_last_mod_date(target_path, match_string, day_cutoff):
    # iterate over items in the directory
    for entry in os.listdir(target_path):
        # check if item name contains the match_string 
        if match_string in entry:
            # get the statistics about the current item
            stat = os.stat(os.path.join(target_path, entry))
            
            # use the item statistics to get the last modified date 
            mod_date = datetime.datetime.fromtimestamp(stat.st_mtime)
            
            # compare the current date to the last modified date and delete item if difference is > day_cutoff
            curr_date = datetime.datetime.now()
            if (curr_date - mod_date).days > day_cutoff:
                if os.path.isdir(os.path.join(target_path, entry)):
                    shutil.rmtree(os.path.join(target_path, entry))
                elif os.path.isfile(os.path.join(target_path, entry)):
                    os.remove(os.path.join(target_path, entry))