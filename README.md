# Greenhouse automation stuff

- [Installing and configuring the automation](#installing-and-configuring-the-automation)
- [Adding your credentials to the automation](#adding-your-credentials-to-the-automation)
- [Duplicating job posts to different locations](#duplicating-job-posts-to-different-locations)
- [Cloning from separate parent posts](#cloning-from-separate-parent-posts)
- [Deleting posts before duplicating](#deleting-posts-before-duplicating)
- [Supported Browsers](#supported-browsers)
- [Available Regions](#available-regions)
- [Additional Troubleshooting](#additional-troubleshooting)

## Installing and configuring the automation
---
```bash
git clone https://github.com/desrod/greenhouse
cd greenhouse
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

If you are using Chrome you'll need to install the appropriate version
of ChromeDriver for your browser, see
https://chromedriver.chromium.org/downloads

Make sure you choose the version that is in the same major version as your installed version of Chrome. 

``` bash
$ google-chrome --version
Google Chrome 95.0.4638.17
```

You can download the matching version, and unpack it into somewhere in your $PATH, or place it in a location you can append to $PATH later. I've put it into `/opt/bin` here: 

``` bash
$ /opt/bin/chromedriver --version
ChromeDriver 95.0.4638.17 (a9d0719444d4b035e284ed1fce73bf6ccd789df2-refs/branch-heads/4638@{#178})
```

You will also need to put this in your default `$PATH`, or export a new `$PATH` environment variable to include this location, eg: 

```bash
export PATH=$PATH:/opt/bin
```

## Adding your credentials to the automation
---
 The [oroginal automation](https://github.com/tvansteenburgh/greenhouse) this repo was forked from used environment variables to hodl the SSO_EMAIL and SSO_PASSWORD. This forked version puts these in a managed file in `~/.local/share/greenhouse/` called `login.tokens`, with the following format: 

``` json
{
    "username": "your.name@canonical.com",
    "password": "So0perSe3kre7P4ssw0rd"
}
```
Keep in mind that any 'foreign' characters you may have in your password may need to be escaped in this file, so it will be parsed correctly. For example, if you have a forward-slash '/' in your password, you'd need to escape that as follows: 

``` yaml
    "password": "So0per\\/Se3kre7\\/P4ssw0rd"
```

The same rule applies for backslashes: 

``` yaml
    "password": "So0per\\\\Se3kre7\\\\P4ssw0rd"
```
Protect this file with your standard operating system permissions. `chmod 0400` should be sufficient to secure it against any unintentional snooping.

## Duplicating job posts to different locations
---
Start with a Greenhouse job with one job posting (the one that will be duplicated).

Get the numeric id for the job. You can get this by going to the job dashboard and copying the id out of the url. It will look something like this:

`https://canonical.greenhouse.io/sdash/1592880`

That number at the end of the url is the job id.

Now run the script and tell it which job id(s) you want to update with new job posts, and which regions you want to post in:

``` bash
./post-job.py 1592880 1726996 --region americas emea
```

> Note: If you're cloning to multiple regions, you **must** provide them at the time of cloning. You cannot clone to 'emea' and then in a second pass, clone to 'americas', as this will fail. 

The browser will open and things will happen:

- Script will log you in to Ubuntu SSO and then pause for you to 2FA.
- New posts will be created for each city in the region that doesn't already have an existing post in that location.
- The new posts (and any others that are currently 'OFF') will be turned ON (made live on the 'Canonical - Jobs' board).
  
  > Note: Please make sure you review the posts when complete, so any that you intended to remain off, are disabled after cloning. 

If the script fails partway through you can safely rerun it, since it won't create a duplicate job post for cities that already have one.

> Note: If the script does fail, it may leave lingering 'chromedriver' processes running. You can kill those off easily with the following: 

``` bash 
kill -9 $(pgrep -f chromedriver)
```
## Cloning from separate parent posts
---
In some cases, you may have a single job that is posted uniquely to specific regions. For example, a DSE role that gets posted to `nycmetro` and `brasil` (both in AMER region), but each post may have their own unique requirements or job description. 

To facilitate this, the automation has a `--limit` flag, which allows you to restrict which post you're targeting when cloning (a "parent" post, in this vernacular). 

To clone a specific post, you'll need to identify two key numeric values: 
1. The `job_id`, found in the URL field of your browser when editing/viewing the role in GH. The `job_id` in the URL if your browser, will look like: 
    ```
    /plans/123456/jobapp
    ```
2. The `app_id`, which you can find by clicking the edit pencil next to the specific parent post you want to clone from. In your browser's URL field, you'll now see a different number that will look like: 

    ```
    /jobapps/543210/edit
    ```
   This second number is the `app_id`. 

3. Knowing these two values, you can then clone with the `--limit` flag using this syntax: 

   ``` 
   ./post-job.py 123456 --region emea --limit 543210 --headless
   ```

I have a Tampermonkey browser add-on that exposes this on each job post to make it easier to clone these roles. Please contact me directly if you want the link to that add-on and wish to use it (link intentionally not posted in this README). 

##  Deleting posts before duplicating
---
Before you clone your posts, you may want to make some changes to the job description, application questions, job naming or other job-specific changes. You'll make those changes in the "parent" post (the source of your clones). 

But you may already have dozens of posts that you duplicated previously. Those will need to be removed and recreated with your latest changes/updates. We also re-clone the job posts on a regular basis to "top-post" them at the various job boards, so they get more attention after they've aged off and gone "below the margin" on those boards. 

To delete and reset your job posts, a preparatory step before re-duplicating (cloning) posts, you can use the following syntax, making sure to use the `job_id`, _not_ the `app_id` here. Using the example from the previous section, that would be: 

```
 ./post-job.py --reset-all 123456 --headless
 ```

This will then go through `job_id: 123456`, remove all posts that are _not_ "parent posts", leaving you with post `543210` (in keeping with the previous example, our parent to be cloned _from_). 

Once your posts have been removed, you can then duplicate them using the steps in the previous secton. 

At the moment, this is a two-step process, while we work out how to limit (using the `--limit` flag described earlier), to filter those posts. 

1. Remove duplicated posts, leaving only the parent post(s) (using `--reset-all`)
2. Re-duplicate your job posts based on those parent post(s) (using `--limit` where needed)

## Supported Browsers
---
Default browser is Chrome but you can alternatively pass the `--browser firefox` option.

This was only tested on Chrome, but may also work with Firefox. YMMV, but report issues you find and we'll fix it! 

## Available Regions
---
The available regions are `americas`, `emea` and `apac`. You can view/update the lists of cities in those regions directly in the source file.

## Additional Troubleshooting
---
If you see an error that looks like: 
```
Traceback (most recent call last):
  File "env/lib/python3.8/site-packages/selenium/webdriver/common/service.py", line 72, in start
    self.process = subprocess.Popen(cmd, env=self.env,
  File "/usr/lib/python3.8/subprocess.py", line 858, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
  File "/usr/lib/python3.8/subprocess.py", line 1704, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: 'chromedriver'
```
This means you haven't yet given the path to `chromedriver` on your system. If you put this in a location already in `$PATH`, it should work, but some like to put these in directories not in the path (such as `/opt/bin/`), and that would need to be exported, as follows: 

```
 export PATH=$PATH:/opt/bin
```
Then re-running the same `post-jobs.py` command will work as expected.
