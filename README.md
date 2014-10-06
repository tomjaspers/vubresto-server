# VUBRESTO-SERVER

Parses the menus for the *Vrije Universiteit Brussel* restaurants **Etterbeek** and **Jette** from the official website to two json files for each language.

- Dutch: https://my.vub.ac.be/resto/{etterbeek, jette}
- English: https://my.vub.ac.be/restaurant/{etterbeek, jette}

# Sample JSON output
```
[
  {
    "date":"2014-09-30",
    "menus":[
      {
        "dish":"Soep van de dag",
        "color":"#fdb85b",
        "name":"Soep"
      },
      {
        "dish":"Hamburger met Archiduc saus",
        "color":"#68b6f3",
        "name":"Dagmenu"
      },
      // etc...
    ]
  },
  // etc...
  ]
  ```

# Install

- Edit *menuparser.py* and set the `SAVE_PATH` variable
- Install requirements `$ pip install -r requirements.txt`
- Ensure permission etc.
- Schedule a cronjob to run the script daily

Voilà, daily restaurant jsons