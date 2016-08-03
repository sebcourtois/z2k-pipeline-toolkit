

from davos.tools import update_damas_users

update_damas_users.launch(dryRun=True)
res = raw_input("Proceed ? (yes/no)")
if res == "yes":
    update_damas_users.launch(dryRun=False)
