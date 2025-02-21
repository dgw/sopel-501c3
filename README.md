# sopel-501c3

501(c)(3) nonprofit lookup plugin for Sopel IRC bots.

Consumes Publication 78 data.

## ⚠️ Important Notice

**Use of this plugin WILL inflate your bot's database size.** It intentionally
uses local storage in lieu of making an HTTP call out to someone's API every
time a command is called.

Importing the whole list of Publication 78 entries into a mostly empty test
instance grew the default SQLite `.db` file to approximately 300 MB. At time of
writing, the list consisted of 1,330,000 items occupying ~94 MB in decompressed
`.txt` format as provided by the IRS. (The final database size also includes
several column indexes, some of which are currently unused.)

## Installing

Releases are hosted on PyPI, so after installing Sopel, all you need is `pip`:

```shell
$ pip install sopel-501c3
```

### Configuring

The easiest way to configure `sopel-501c3` is via Sopel's configuration
wizard—simply run `sopel-plugins configure 501c3` and enter the values for which
it prompts you.

Only one option is present in the interactive wizard at this time:

* `update_interval`: how often (in days) the plugin should redownload the
  Publication 78 data file and merge the contents with its database

### First startup

The first time Sopel is run with this plugin enabled, the plugin will
immediately fetch the latest Publication 78 data and start populating its
database table. This is a **blocking** update, and the bot will not continue
with startup until the data import is finished. Finishing the initial data
import could take several minutes—or longer, depending on system performance.

If interrupted (e.g. by pressing <kbd>Ctrl</kbd>+<kbd>C</kbd>), the initial
import will resume the next time Sopel is started—still in a blocking mode.
Entries already added will be checked again; while re-checking entries is
somewhat faster than adding new ones, letting the initial data load complete in
a single go will ultimately require the smallest amount of wall time.

After the *full* initial import finishes once, subsequent updates are run in a
background thread.

## Using

`sopel-501c3` provides one command with two names:

* `.501c3`/`.npo`: If passed an EIN, looks up that EIN. Otherwise, looks for
  nonprofits whose names contain the query as a substring and responds with up
  to three of them.

Fuzzier search would be a desirable feature someday, but this initial
implementation doesn't attempt it.

Likewise, the ability to "page" past the first three search results would be
handy, but that's a project for the future (or perhaps an eager contributor).

## Uninstalling

If you wish to remove this plugin, but keep using the bot instance for other
tasks, it's recommended to ``DROP TABLE `501c3_npos`;`` after the plugin is
deactivated/deleted.

How to do this will depend on the database backend you're using. For Sopel's default SQLite backend, that would look like:

**⚠️ WARNING: Destructive command with no confirmation step!**

```bash
sqlite3 /path/to/.sopel/configname.db "DROP TABLE '501c3_npos';" "VACUUM;"
```

Replace `configname` with the name of your Sopel config. If you don't specify
one when starting your bot (no `-c` argument), the name is probably `default`.

This one-liner removes the `sopel-501c3` table with all of its data, and
compacts the database file. (**Note:** `VACUUM` [could
require](https://www.sqlite.org/lang_vacuum.html#how_vacuum_works) up to 2x the
original file size in temporary disk space.)

Run against the same test instance [mentioned earlier](#️-important-notice),
doing this reduced the `.db` file from ~300 MB back down to ~50 KB.
