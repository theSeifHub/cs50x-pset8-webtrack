# C$50 Finance

Implement a website via which users can “buy” and “sell” stocks. [More...](https://cs50.harvard.edu/x/2020/tracks/web/finance/)

## Getting started (on Windows):

1. Clone the repo.
2. Assuming you have [Python 3](https://www.python.org/downloads/) installed; install [`venv`](https://docs.python.org/3/library/venv.html) in your work directory. In your terminal, execute:
   ```
   py -3 -m venv venv
   ```
3. Activate the virtual environment. Execute:
   ```
   venv\Scripts\activate
   ```
4. Install the following:
   - Flask:
     ```
     pip install Flask
     ```
   - Flask_session:
     ```
     pip install Flask-Session
     ```
   - cs50:
     ```
     pip install cs50
     ```
   - requests:
     ```
     pip install requests
     ```
5. Register for an API key to query [IEX](https://iexcloud.io/)’s data:
   - Visit iexcloud.io/cloud-login#/register/.
   - Enter your email address and a password, and click “Create account”.
   - On the next page, scroll down to choose the Start (free) plan.
   - Once you’ve confirmed your account via a confirmation email, sign in to iexcloud.io.
   - Click API Tokens.
   - Copy the key that appears under the Token column (it should begin with pk\_).
6. Set the _API_KEY_ in your application. In a terminal, execute:

   ```
   export API_KEY=value
   ```

   replacing `value` with the api key you copied

7. To start your local server; execute:
   ```
   Flask run
   ```
