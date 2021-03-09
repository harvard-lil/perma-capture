<template>
<TheNavbar/>
<TheMainHeader
  head="User Guide"/>
<main>
  <div class="row mt-5">
    <div class="col-sm-4">
      <h2 class="h4">Table of Contents</h2>
      <ul class="list-unstyled">
        <li><a href="#capturing-urls">Capturing URLs</a>
          <ul>
            <li><a href="#capturing-ui">Using the Web Interface</a></li>
            <li><a href="#capturing-api">Using the API</a>
              <ul>
                <li><a href="#capturing-auth">Authorization</a></li>
                <li><a href="#capturing-endpoints">Endpoints</a></li>
              </ul>
            </li>
            <li><a href="#capturing-advanced-features">Advanced Features</a>
              <ul>
                <li><a href="#capturing-oembed">oEmbed Captures</a></li>
                <li><a href="#webhook-notifications">Webhooks</a></li>
                <li><a href="#zapier-integration">Zapier Integration</a></li>
              </ul>
            </li>
            <li><a href="#capturing-under-development">Features in Development</a>
              <ul>
                <li>Archive Hashes</li>
              </ul>
            </li>
          </ul>
        </li>
        <li><a href="#viewing-captured-urls">Viewing Captured URLs</a>
          <ul>
            <li><a href="#embed-instructions">How to Embed</a></li>
            <li><a href="#embed-examples">Examples</a>
              <ul>
                <li>Glitch</li>
              </ul>
            </li>
          </ul>
        </li>
      </ul>
    </div>
    
    <div class="col">
      
      <p class="lead">The Perma.cc capture system is built on <a href="https://github.com/webrecorder">Webrecorder</a> technology and uses an automated browser to produce high-fidelity web archives.</p>
      <p>A <a href="https://github.com/webrecorder/wacz-format">web archive file</a> is created for each submitted URL, and each archive can be downloaded, embedded in a web page and displayed ("replayed") by any <a href="https://caniuse.com/serviceworkers">modern browser</a>.</p>
      
      <h2 id="capturing-urls">Capturing URLs</h2>
      
      <h3 id="capturing-ui">Using the Web Interface</h3>
      <p>After logging in, simply <router-link :to="{name: 'dashboard'}">enter the URLs</router-link> you'd like to preserve and click "Capture." A capture job will be launched for each submitted URL.</p>
      <p>A list of all your active capture jobs will appear beneath the form. When each job is finished, you can click <img style="width: 1.5em; height: 1.5em; vertical-align: top" alt="the preview button" title="Preview Capture" src="../assets/img/preview.svg"> to preview the capture, and <img style="width: 1.1em; height: 1.1em" alt="the download button" title="Download Capture" src="../assets/img/download.svg"> to download the web archive file.</p>
      <p><img style="max-width: 100%;" src="../assets/img/dashboard-screenshot.png" alt="Screenshot of the dashboard. The 'create a new archive' form is above a list of 2 capture jobs, with their download and preview buttons circled."></p>
      <p>Capture jobs are retained for 4 hours and then are automatically deleted. Deleted capture jobs cannot be recovered from the service.</p>
      <p>Read more about other options under <a href="#capturing-advanced-features">advanced features</a> and <a href="#capturing-under-development">features in development</a>.</p>
      
      
      <h3 id="capturing-api">Using the API</h3>
      
      <p v-if="auth_token_key"><em>Your API Key is <code>{{ auth_token_key }}</code></em></p>
      
      <h4 id="capturing-auth">Authorization </h4>
      
      <p>All registered users receive an <router-link :to="{name: 'account'}">API key</router-link>. Every request to the API must be authenticated by providing that key as part of the <code>Authorization</code> header:</p>
      
      <pre><code>curl -H "Authorization: Token {{ auth_token_key }}" {{ base_url }}...
      </code></pre>
      
      <h4 id="capturing-endpoints">Endpoints</h4>
      
      <p>You can create archives programmatically by sending an HTTP <code>POST</code> to <code>{{ base_url + '/captures/'}}</code>.</p>
      
      <p>Required data (JSON-formatted): <code>"urls"</code> (a list of URLs to capture, each explicitly prefixed by <code>http</code> or <code>https</code>).</p>
      
      <p>Optionally, you may also specify a <code>"tag"</code> (a nickname for this batch of URLs, for your convenience). If you are subscribed to <a href="#webhook-notifications">webhook notifications</a>, you may also optionally specify a <code>"userDataField"</code> for your convenience (a string you would like included, verbatim, in the webhook notification response).</p>
      
      <p>Here's a request to archive a small batch of two URLs using <code>curl</code>:</p>
      
      <pre><code>curl -X POST \
          -H "Content-Type: application/json" \
          -H "Authorization: Token {{ auth_token_key }}" \
          --data '{ \
          "urls": [ \
          "https://twitter.com/permacc", \
          "https://example.com/" \
          ], \
          "tag": "my-batch", \
          "userDataField": "foo=bar&boo=baz" \
          }' \
          {{ base_url + '/captures/' }}
      </code></pre>
      
      <p>The response, on success, will be a JSON dictionary including a jobid for each submitted URL:</p>
      
      <pre><code>{
          "urls": 2,
          "jobids": ["uuid4-1", "uuid4-2"]
          }
      </code></pre>
      
      <p>You can then query <code>{{ base_url + '/captures/' }}</code> to see all the capture jobs you have in the system:</p>
      
      <pre><code>curl -H "Authorization: Token {{ auth_token_key }}" {{ base_url + '/captures/' }}
      </code></pre>
      
      <p>Sample Response:</p>
      <pre><code>{
          "jobs": [{
          "jobid": "uuid4-1",
          "userid": "3",
          "captureUrl": "https://twitter.com/permacc",
          "useEmbeds": false,
          "userTag": "my-batch",
          "startTime": "2020-09-28T23:54:19+00:00",
          "elapsedTime": "2020-09-28T23:56:45+00:00",
          "accessUrl": null,
          "status": "In progress"
          }, {
          "jobid": "uuid4-2",
          "userid": "3",
          "captureUrl": "https://example.com/",
          "useEmbeds": false,
          "userTag": "my-batch",
          "startTime": "2020-09-28T23:54:19+00:00",
          "elapsedTime": "2020-09-28T23:54:39+00:00",
          "status": "Complete",
          "accessUrl": "https://permacaptures.example.com/path/to/download/mycapture.wacz"
          }]
          }
      </code></pre>
      
      <p>The response will list all active capture jobs created by your account. Each job will have a <code>"status"</code> field, set to either <code>In progress</code>, <code>Failed</code>, or <code>Complete</code>.</p>
      
      <p>A job that is <code>In progress</code> should be monitored until it is <code>Complete</code>. (Or, if you'd like to be notified when a job is complete, check out <a href="#webhook-notifications">webhook notifications</a>.) A <code>Failed</code> job indicates a permanent failure to produce a capture: you may wish to retry.</p>
      
      <p>A job that is <code>Complete</code> will have an <code>accessUrl</code> set to a downloadable URL. The download URL is valid for 4 hours after the job is completed.</p>
      
      <p>All information about a capture job is automatically deleted after 4 hours. (Learn more about the <a href="#archive-hashes">information we retain</a>.)</p>
      
      <p>Read more about other options under <a href="#capturing-advanced-features">advanced features</a> and <a href="#capturing-under-development">features in development</a>.</p>
      
      
      <h3 id="capturing-advanced-features">Advanced Features</h3>
      
      <h4 id="capturing-oembed">Capture of "Embeddable" Views</h4>
      
      <p>Many websites offer an easily-embeddable "<a href="https://oembed.com/">oEmbed</a>" view of snippets of their content. For example, Twitter provides the following embeddable view of the Tweet at <a href="https://twitter.com/permacc/status/1039225277119954944">https://twitter.com/permacc/status/1039225277119954944</a>:</p>
      
      <blockquote class="twitter-tweet"><p lang="en" dir="ltr">Are you someone who cites to the internet a lot? The web&#39;s a wonderful resource but can be more fragile than you think. Anyone working in <a href="https://twitter.com/hashtag/academia?src=hash&amp;ref_src=twsrc%5Etfw">#academia</a>, <a href="https://twitter.com/hashtag/journalism?src=hash&amp;ref_src=twsrc%5Etfw">#journalism</a>, <a href="https://twitter.com/hashtag/legaltech?src=hash&amp;ref_src=twsrc%5Etfw">#legaltech</a>- any industry that depends on reliable citations should be on the offense against <a href="https://twitter.com/hashtag/linkrot?src=hash&amp;ref_src=twsrc%5Etfw">#linkrot</a>, Perma can help! <a href="https://t.co/XVwEwa2zEA">pic.twitter.com/XVwEwa2zEA</a></p>&mdash; Perma.cc (@permacc) <a href="https://twitter.com/permacc/status/1039225277119954944?ref_src=twsrc%5Etfw">September 10, 2018</a></blockquote>
      
      <p>When submitting URLs for capture, you may indicate that when a target website provides support for an "oEmbed" view, the web archive should include a capture of that view, along with the standard web view.</p>
      
      <p>Using the web interface: check the "Archive Embedded Version" box. Using the API: include <code>"embeds": true</code> in your <code>POST</code> data.</p>
      
      <p>Capture via oEmbed is currently supported for Twitter, Instagram, Facebook, YouTube, and SlideShare. Additional domains may be supported in the future; an up-to-date list of <a href="https://github.com/ikreymer/permafact-backend/blob/master/driver/embeds.json">supported domains and URL patterns</a> is available on Github.</p>
      
      <h4 id="webhook-notifications">Webhook Notifications</h4>
      
      <p>We can notify you when your capture jobs are complete by sending an HTTP <code>POST</code>to a callback URL you specify.</p>
      
      <p>To subscribe to the <code>ARCHIVE_CREATED</code> event, <code>POST</code> your callback URL to <a href="/webhooks/">{{ base_url + '/webhooks/' }}</a>.</p>
      
      <pre><code>curl -X POST \
          -H "Content-Type: application/json" \
          -H "Authorization: Token {{ auth_token_key }}" \
          --data '{ \
          "callbackUrl": https://mysite.com/callback", \
          "eventType": "ARCHIVE_CREATED"
          }' \
          {{ base_url + '/webhooks/' }}
      </code></pre>
      
      <p>We'll send back a subscription <code>id</code>, as well as a <code>signingKey</code> and <code>signingKeyAlgorithm</code> that you can optionally use to verify that any <code>POST</code> received by your callback URL is really from us.</p>
      
      <pre><code>{
          "id": 53,
          "user": 3,
          "eventType": "ARCHIVE_CREATED",
          "signingKey": "a-128-character-key"
          "signingKeyAlgorithm": "sha256"
          }
      </code></pre>
      
      <p>You can subscribe as many times as you like, if you'd like multiple callback URLs to be notified.</p>
      
      <p>When an archive you request is complete, we'll make a <code>POST</code> to your callback like the following:</p>
      
      <pre><code>{
          "userid": 3,
          "jobid": "uuid4-1",
          "url": "http://cnn.com",
          "accessUrl": "https://permacaptures.example.com/path/to/download/mycapture.wacz",
          "userDataField": ""
          }
      </code></pre>
      
      <p>We will include the signature in the <code>X-Hook-Signature</code> header.</p>
      
      <p>If you want to verify the signature before acting, here's how to do it in Python:</p>
      
      <pre><code>import hmac
          import urllib
          def is_valid_signature(signature, data, signing_key, signing_key_algorithm):
          return hmac.compare_digest(
          signature,
          hmac.new(
          bytes(signing_key, 'utf-8'),
          bytes(urllib.parse.urlencode(data, doseq=True), 'utf-8'),
          signing_key_algorithm
          ).hexdigest()
          )
      </code></pre>
      
      <p>...and JavaScript:</p>
      
      <pre><code>const crypto = require('crypto');
          const querystring = require('querystring');
          function isValidSignature(signature, data, signingKey, signingKeyAlgorithm){
          const postedSignature = Buffer.from(signature, 'utf-8');
          const generatedSignature = Buffer.from(
          crypto
          .createHmac(signingKeyAlgorithm, signingKey)
          .update(querystring.stringify(data))
          .digest('hex'),
          'utf-8'
          );
          try {
          return crypto.timingSafeEqual(postedSignature, generatedSignature);
          } catch (e) {
          return false;
          }
          }
      </code></pre>
      
      <p>If you no longer wish to receive notifications, you can delete your subscription:</p>
      
      <pre><code>curl -X DELETE -H "Authorization: Token {{ auth_token_key }}" {{ base_url + '/webhooks/53' }}
      </code></pre>
      
      <h4 id="zapier-integration">Zapier Integration</h4>
      
      <p><a href="https://zapier.com">Zapier</a> users can integrate the Perma.cc capture service in their workflows.</p>

<p>For example, using this Zap, you can <a href="https://zapier.com/shared/3ee9336c0d9734d9fe6cc86e672b530f8336e93b">archive a URL straight from Slack</a>, and this Zap will follow up, posting a <a href="https://zapier.com/app/editor/108033832/nodes/108033832">link to the completed archive as a reply</a>, when it's finished.</p>

<p><img style="max-width: 100%;" src="../assets/img/slack-screenshot.png" alt="Screenshot of Slack, showing a capture request and a threaded reply with a link to the archive."></p>

<p>This Zap, on the other hand, will post to a pre-configured Slack channel of your choice whenever <a href="https://zapier.com/shared/e1ccf1faa9b236b2317b85b46f0a643e8259aa77">an archive created by your account is ready to be downloaded</a>.</p>

<p>Let us know if you are interested in a Zapier integration, and we'll help you get started!</p>

<p>Note: Zapier does not support <a href="http://resthooks.org/docs/security/">signature validation</a>, instead relying on the privacy of subscription URLs for security. If you need to further verify the authenticity of data triggering your workflows, we recommend working with our webhooks directly.</p>

<h3 id="capturing-under-development">Features in Development</h3>

<h4 id="archive-hashes">Archive Hashes</h4>

<p>We maintain a <code>sha-256</code> hash of every web archive file produced by the service, along with the timestamp of its production and the user id of the requesting user. We don't store any other metadata about capture jobs, including the target URL.</p>

      <p>We selected <code>sha256</code>, despite its known limitations, because we wanted the algorithm to be <a href="https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest">supported in JavaScript</a>, and we weren't sure it was reasonable to expect users attempting to verify file hashes to manually calculate <code>sha512/256</code>.</p>
  
<p>Let us know if that sounds correct to you!</p>

<hr>

<h2 id="viewing-captured-urls">Viewing Captured URLs</h2>

<p>The downloadable WACZ files can be embedded in your site using the <a href="https://replayweb.page">ReplayWeb.page</a> embed system, loaded directly from NPM.</p>


<h3 id="embed-instructions">How to Embed</h3>

<ol>
  <li>The replay system requires you to host a single JavaScript file on your server, which visitors browsers will use to install the service worker that handles playbacks. We recommend putting it in an empty directory, for example at <code>/replay/sw.js</code>. This file must be named <code>sw.js</code>, and it should contain the following:
    <pre><code>importScripts("{{ rwp_base_url }}/sw.js");
  </code></pre></li>
  
  <li>Each page that will contain embedded archives should include the following script and should also set the height for the <code>replay-web-page</code> tag to ensure a minimum height.
    (600px is used as an example here).
    <pre><code>&lt;script src="{{ rwp_base_url }}/ui.js"&gt;&lt;/script&gt;
        &lt;style&gt;
        replay-web-page {
        height: 600px;
        display: flex;
        }
        &lt;/style&gt;
  </code></pre></li>
  
  <li>For each web archive/WACZ you'd like to embed, simply add the following HTML snippet:
    
    <pre><code>&lt;replay-web-page
        source="https://mysite.example.com/path/to/archives/mycapture.wacz"
        url="https://example.com/"
        replayBase="/replay/"
        /&gt;
  </code></pre></li>
    
</ol>

<p>The <code>source</code> attribute should point to the URL of where the WACZ file is hosted, while the <code>url</code> is the URL captured.
  The <code>replayBase</code> is the path that contains the <code>sw.js</code> file. (<code>/replay/</code> in this example is also the default, and therefore could be omitted.)</p>

<p>The web server hosting WACZ files must support HTTP/1.1 range requests and be able to read portions of a file. If the WACZ file is hosted on a different domain than your site, CORS rules will also need to be enabled on the hosting server.</p>


<h3 id="embed-examples">Examples</h3>

<p>The following two archives were created using this system:</p>

<ul>
  <li><a href="https://permafact-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz">https://permafact-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz</a></li>
  <li><a href="https://permafact-demo.s3.amazonaws.com/www.youtube.com-2020-09-03.wacz">https://permafact-demo.s3.amazonaws.com/www.youtube.com-2020-09-03.wacz</a></li>
</ul>

<p>We'll embed a replay of the first archive using the following code:</p>

<pre><code>&lt;replay-web-page
    source="https://permafact-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz"
    url="https://twitter.com/dog_rates/status/1298052245209006086?s=20"
    &gt;&lt;/replay-web-page&gt;
</code></pre>

<replay-web-page
  source="https://permafact-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz"
  url="https://twitter.com/dog_rates/status/1298052245209006086?s=20"
  replayBase="{{ rwp_base_url }}/"
  ></replay-web-page>

<p>The service worker is loaded from <a :href="sw_path"><code>{{ sw_path }}</code></a>. Since that's the default path, no further configuration is needed.</p>

    <p>We'll embed a replay of the second archive using the following code:</p>

<pre><code>&lt;replay-web-page
  source="https://permafact-demo.s3.amazonaws.com/www.youtube.com-2020-09-03.wacz"
  url="https://www.youtube.com/watch?v=dIUwVMDI7yE",
  replayBase="/replay/"
&gt;&lt;/replay-web-page&gt;
</code></pre>

    <replay-web-page
      source="https://permafact-demo.s3.amazonaws.com/www.youtube.com-2020-09-03.wacz"
      url="https://www.youtube.com/watch?v=dIUwVMDI7yE"
      replayBase="{{ rwp_base_url }}/"
    ></replay-web-page>

    <p>Here, we redundantly configure <code>replayBase</code> to point to <code>/replay/</code>, the path where <code>sw.js</code> for demonstration purposes.</p>

    <h4>Glitch</h4>

    <p>A fully stand-alone example of these embeds is also available on <a href="https://permafact-demo.glitch.me/">Glitch</a>.</p>
    </div>
  </div>
</main>
</template>

<script lang="ts">
import TheNavbar from './TheNavbar.vue'

export default {
  components: {
    TheNavbar
  },
  data: () => ({
    rwp_base_url: '',
    sw_path: '',
    auth_token_key: 'your-api-key'
  }),
  computed: {
    base_url: () =>
      window.location.origin
  }
}
// script async src="https://platform.twitter.com/widgets.js" charset="utf-8"
</script>

<style>
/* Fixes overflow: auto not working on code blocks */
.col {
  min-width: 0
}

h2:not(:first-child) {
  margin-top: 3rem;
}
h3 {
  margin-top: 2rem;
}
h4 {
  margin-top: 1.5rem;
}

pre {
  padding: 1rem;
  background-color: var(--color-background);
}
</style>
