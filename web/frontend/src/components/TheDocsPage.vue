<template>
  <div class="container-full docs-page-container">
    <div class="docs container">
      <ul class="table-of-contents">
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

      <div class="content">

        <TheMainHeader head="User Guide" :center="false"/>

        <p class="lead">The Perma.cc capture system is built on <a href="https://github.com/harvard-lil/scoop">Scoop</a> and uses an automated browser to produce high-fidelity web archives.</p>

        <p>A compressed <a href="https://github.com/webrecorder/wacz-format">web archive file</a> (WACZ) is created for each submitted URL, and each archive can be downloaded, embedded in a web page and displayed ("replayed") by any <a href="https://caniuse.com/serviceworkers">modern browser</a>.</p>

        <h2 id="capturing-urls">Capturing URLs</h2>

        <h3 id="capturing-ui">Using the Web Interface</h3>

        <p>After logging in, simply
          <router-link :to="{name: 'root'}">enter the URLs</router-link>
          you'd like to preserve and click "Create." A capture job will be launched for each submitted URL.
        </p>

        <p>A list of all your active capture jobs will appear next to the form. When each job is finished, you can click the chevron to see a preview of the capture and download the web archive file.
        </p>

        <p>
          <img style="max-width: 100%;" src="../assets/img/dashboard-screenshot-expand.png"
               alt="Screenshot of the dashboard. The 'create a new archive' form is next to a list of 2 capture jobs, with their 'expand details' button circled.">
        </p>

        <p>
          <img style="max-width: 100%;" src="../assets/img/dashboard-screenshot-download.png"
               alt="Screenshot of the dashboard with a capture job's details expanded. The 'downlad' button is circled.">
        </p>

        <p>Web archive files are retained for 4 hours and then are automatically deleted. Deleted archives cannot be recovered from the service. Metadata, however, is retained indefinitely.</p>

        <h3 id="capturing-api">Using the API</h3>

        <p v-if="auth_token"><em>Your API Key is <code>{{ auth_token.key }}</code>.</em></p>

        <h4 id="capturing-auth">Authorization </h4>

        <p>All registered users receive an <router-link :to="{name: 'account'}">API key</router-link>. Every request to the API must be authenticated by providing that key as part of the <code>Authorization</code> header:
        </p>

        <pre><code>curl -H "Authorization: Token {{ auth_token_key }}" {{ base_url }}...</code></pre>

        <h4 id="capturing-endpoints">Endpoints</h4>

        <p>You can create archives programmatically by sending an HTTP <code>POST</code> to <code>{{ base_url + '/captures/' }}</code>.</p>

        <p>A minimal capture request using <code>curl</code>:</p>

        <pre><code>
curl -X POST http://localhost:8000/captures/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token c27a765c26bd8aeee8859ca55e7d06ec2a4852a8" \
     --data '{"requested_url":"example.com"}'
        </code></pre>

        <p>Optionally, you may configure a number of advanced capture options, and may specify a <code>label</code> to associate with the capture for your convenience (for instance, labeling a group of related captures). If you are subscribed to <a href="#webhook-notifications">webhook notifications</a>, you may also optionally specify <code>webhook_data</code> for your convenience (a string you would like included, verbatim, in the webhook notification response).</p>

        <p>You may submit capture requests singly or in batches.</p>

        <p>Here's a request to archive a small batch of two URLs. The first toggles all currently available advanced options to their non-default values.</p>

        <pre><code>
curl -X POST {{ base_url + '/captures/' }} \
-H "Content-Type: application/json" \
-H "Authorization: Token {{ auth_token_key}}" \
--data-binary @- &lt;&lt; EOF
[
    {
        "requested_url":"example.com",
        "label": "my-batch",
        "include_raw_exchanges": true,
        "include_screenshot": false,
        "include_pdf_snapshot": true,
        "include_dom_snapshot": true,
        "include_videos_as_attachment": false,
        "include_certificates_as_attachment": false,
        "run_site_specific_behaviors": false
    }, {
        "requested_url":"https://twitter.com/permacc",
        "label": "my-batch",
        "webhook_data": "foo=bam&boo=bap"
    }
]
EOF
        </code></pre>

        <p>The response, on success, will be a JSON dictionary including an ID for each request, the status of the request (<code>pending</code>, <code>in_progress</code>, <code>completed</code>, <code>failed</code>, or <code>invalid</code>), and all the configuration options. Example: </p>

        <pre><code>
{
  "id": 16,
  "requested_url": "example.com",
  "validated_url": null,
  "human": false,
  "include_raw_exchanges": false,
  "include_screenshot": true,
  "include_pdf_snapshot": false,
  "include_dom_snapshot": false,
  "include_videos_as_attachment": true,
  "include_certificates_as_attachment": true,
  "run_site_specific_behaviors": true,
  "headless": true,
  "label": null,
  "webhook_data": null,
  "status": "pending",
  "message": null,
  "queue_position": 1,
  "step_count": 0,
  "step_description": null,
  "created_at": "2023-05-10T16:00:22.134813Z",
  "updated_at": "2023-05-10T16:00:22.134831Z",
  "capture_start_time": null,
  "capture_end_time": null,
  "archive": null
}
        </code></pre>

        <p>You can query <code>{{ base_url + '/captures/' }}</code> to see all the capture jobs you have in the system:</p>

        <pre><code>curl -H "Authorization: Token {{ auth_token_key }}" {{ base_url + '/captures/' }}</code></pre>

        <p>Sample Response:</p>
        <pre><code>
[
  {
    "id": 15,
    "requested_url": "example.com",
    "validated_url": "http://example.com",
    "human": false,
    "include_raw_exchanges": false,
    "include_screenshot": true,
    "include_pdf_snapshot": false,
    "include_dom_snapshot": false,
    "include_videos_as_attachment": true,
    "include_certificates_as_attachment": true,
    "run_site_specific_behaviors": true,
    "headless": true,
    "label": "",
    "webhook_data": null,
    "status": "completed",
    "message": null,
    "queue_position": 0,
    "step_count": 20,
    "step_description": "Saving screenshot.",
    "created_at": "2023-05-10T16:00:01.904961Z",
    "updated_at": "2023-05-10T16:00:06.650394Z",
    "capture_start_time": "2023-05-10T16:00:01.989230Z",
    "capture_end_time": "2023-05-10T16:00:06.650624Z",
    "archive": {
      "id": 14,
      "hash": "56052c28e76ac4bebd4551f4d834e7e8cf9683dc1a41a30a901500152b372fcf",
      "hash_algorithm": "sha256",
      "size": 34036,
      "download_url": "http://localhost:9000/perma-capture/archives/job-15-example-com.wacz?AWSAccessKeyId=accesskey&Signature=BruX09kwS8naC5xXl9xtTMGLnoE%3D&Expires=1683748806",
      "download_expiration_timestamp": "2023-05-10T20:00:06Z",
      "created_at": "2023-05-10T16:00:06.559135Z",
      "updated_at": "2023-05-10T16:00:06.559144Z",
      "partial_capture": false,
      "target_url_content_type": "text/html; charset=UTF-8",
      "entrypoints": {
        "web_capture": "http://example.com/",
        "screenshot": "file:///screenshot.png",
        "provenance_summary": "file:///provenance-summary.html"
      },
      "noarchive_urls": [],
      "title": "Example Domain",
      "description": null,
      "wacz_version": "1.1.1",
      "capture_software": "Scoop @ Harvard Library Innovation Lab: 0.3.1",
      "screenshot_url": "http://localhost:9000/perma-capture/screenshots/archive_14/screenshot.png?AWSAccessKeyId=accesskey&Signature=Nh6mIRusqLHt9MWrVJPtH78dYDM%3D&Expires=1683738141"
    }
  },
  {
  "id": 16,
  "requested_url": "example.com",
  "validated_url": null,
  "human": false,
  "include_raw_exchanges": false,
  "include_screenshot": true,
  "include_pdf_snapshot": false,
  "include_dom_snapshot": false,
  "include_videos_as_attachment": true,
  "include_certificates_as_attachment": true,
  "run_site_specific_behaviors": true,
  "headless": true,
  "label": null,
  "webhook_data": null,
  "status": "pending",
  "message": null,
  "queue_position": 1,
  "step_count": 0,
  "step_description": null,
  "created_at": "2023-05-10T16:00:22.134813Z",
  "updated_at": "2023-05-10T16:00:22.134831Z",
  "capture_start_time": null,
  "capture_end_time": null,
  "archive": null
  }
]
        </code></pre>

        <p>A job that is <code>in_progress</code> should be monitored until it is <code>completed</code>. (Or, if you'd like to be notified when a job is complete, check out <a href="#webhook-notifications">webhook notifications</a>.) A <code>failed</code> job indicates a permanent failure: you may wish to retry.</p>

        <p>A job that is <code>completed</code> will include information on the associated web archive, including its <code>download_url</code> and <code>download_expiration_timestamp</code>.</p>

        <p>The download URL is valid for 4 hours after the job is completed, after which the web archive files is automatically deleted. Deleted archives cannot be recovered from the service. Metadata, however, is retained indefinitely.</p>

        <h3 id="capturing-advanced-features">Advanced Features</h3>

        <h4 id="webhook-notifications">Webhook Notifications</h4>

        <p>We can notify you when your capture jobs are complete by sending an HTTP <code>POST</code>to a callback URL you specify.</p>

        <p>To subscribe to the <code>ARCHIVE_CREATED</code> event, <code>POST</code> your callback URL to <a href="/webhooks/">{{ base_url + '/webhooks/' }}</a>.</p>

        <pre><code>
curl -X POST {{ base_url + '/webhooks/' }} \
     -H "Content-Type: application/json" \
     -H "Authorization: Token {{ auth_token_key }}" \
     --data '{"callback_url": "https://webhookservice.com?hookid=1234", "event_type": "ARCHIVE_CREATED"}'
        </code></pre>

        <p>We'll send back a subscription <code>id</code>, as well as a <code>signing_key</code> and <code>signing_key_algorithm</code> that you can optionally use to verify that any <code>POST</code> received by your callback URL is really from us.</p>

        <pre><code>
{
  "id": 2,
  "created_at": "2023-05-10T16:32:49.289925Z",
  "updated_at": "2023-05-10T16:32:49.289944Z",
  "event_type": "ARCHIVE_CREATED",
  "callback_url": "https://webhookservice.com?hookid=1234",
  "signing_key": "14135949d61787acc592defd569d3686c8c61ca9d1b8f7e0e51d318a1391037553a8a3b3c6073d7f86679ec76e08144cb85f7193491e421a11667c7abc8a8224",
  "signing_key_algorithm": "sha256"
}
        </code></pre>

        <p>You can subscribe as many times as you like, if you'd like multiple callback URLs to be notified.</p>

        <p>When an archive you request is complete, we'll make a <code>POST</code> to your callback like the following:
        </p>

        <pre><code>
{
  "webhook": {
    "id": 2,
    "event_type": "ARCHIVE_CREATED"
  },
  "capture_job": {
    "id": 18,
    "requested_url": "example.com",
    "validated_url": "http://example.com",
    "human": false,
    "include_raw_exchanges": false,
    "include_screenshot": true,
    "include_pdf_snapshot": false,
    "include_dom_snapshot": false,
    "include_videos_as_attachment": true,
    "include_certificates_as_attachment": true,
    "run_site_specific_behaviors": true,
    "headless": true,
    "label": "",
    "webhook_data": null,
    "status": "in_progress",
    "message": null,
    "queue_position": 0,
    "step_count": 19,
    "step_description": "Saving summary metadata.",
    "created_at": "2023-05-10T16:37:05.968035Z",
    "updated_at": "2023-05-10T16:37:10.141362Z",
    "capture_start_time": "2023-05-10T16:37:06.036673Z",
    "capture_end_time": null,
    "archive": {
      "id": 17,
      "hash": "49d09036e1c2d884b8b2efc993ced21288086c4e7a8a989e72818a783ac72dd6",
      "hash_algorithm": "sha256",
      "size": 34040,
      "download_url": "http://localhost:9000/perma-capture/archives/job-18-example-com.wacz?AWSAccessKeyId=accesskey&Signature=np4mDrQsebLgdK5I1zXT26YBQVQ%3D&Expires=1683751030",
      "download_expiration_timestamp": "2023-05-10T20:37:10Z",
      "created_at": "2023-05-10T16:37:10.143777Z",
      "updated_at": "2023-05-10T16:37:10.143786Z",
      "partial_capture": false,
      "target_url_content_type": "text/html; charset=UTF-8",
      "entrypoints": {
        "web_capture": "http://example.com/",
        "screenshot": "file:///screenshot.png",
        "provenance_summary": "file:///provenance-summary.html"
      },
      "noarchive_urls": [],
      "title": "Example Domain",
      "description": null,
      "wacz_version": "1.1.1",
      "capture_software": "Scoop @ Harvard Library Innovation Lab: 0.3.1",
      "screenshot_url": null
    }
  }
}
        </code></pre>

        <p>We will include the signature in the <code>x-hook-signature</code> header.</p>

        <p>If you want to verify the signature before acting, here's how to do it in Python:</p>

        <pre><code>
import hmac
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

        <pre><code>
const crypto = require('crypto');
const querystring = require('querystring');

function isValidSignature(signature, data, signingKey, signingKeyAlgorithm){
  const postedSignature = Buffer.from(signature, 'utf-8');
  const generatedSignature = Buffer.from(
    crypto.createHmac(signingKeyAlgorithm, signingKey).update(querystring.stringify(data)).digest('hex'),
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

        <pre><code>curl -i -X DELETE -H "Authorization: Token {{ auth_token_key }}" {{ base_url + '/webhooks/2' }}</code></pre>

        <p>Sample response:</p>

        <pre><code>
HTTP/1.1 204 No Content
Date: Wed, 10 May 2023 16:43:36 GMT
Content-Length: 0
        </code></pre>

        <h4 id="zapier-integration">Zapier Integration</h4>

        <p><a href="https://zapier.com">Zapier</a> users can integrate the Perma.cc capture service in their workflows.
        </p>

        <p>For example, using this Zap, you can <a href="https://zapier.com/shared/3ee9336c0d9734d9fe6cc86e672b530f8336e93b">archive a URL straight from Slack</a>, and this Zap will follow up, posting a <a href="https://zapier.com/app/editor/108033832/nodes/108033832">link to the completed archive as a reply</a>, when it's finished.</p>

        <p>
          <img style="max-width: 100%;" src="../assets/img/slack-screenshot.png"
               alt="Screenshot of Slack, showing a capture request and a threaded reply with a link to the archive."
          >
        </p>

        <p>This Zap, on the other hand, will post to a pre-configured Slack channel of your choice whenever <a href="https://zapier.com/shared/e1ccf1faa9b236b2317b85b46f0a643e8259aa77">an archive created by your account is ready to be downloaded</a>.</p>

        <p>Let us know if you are interested in a Zapier integration, and we'll help you get started!</p>

        <p>Note: Zapier does not support <a href="http://resthooks.org/docs/security/">signature validation</a>, instead relying on the privacy of subscription URLs for security. If you need to further verify the authenticity of data triggering your workflows, we recommend working with our webhooks directly.</p>

        <h3 id="capturing-under-development">Features in Development</h3>

        <h4 id="archive-hashes">Archive Hashes</h4>

        <p>We maintain a <code>sha-256</code> hash of every web archive file produced by the service.</p>

        <p>We selected <code>sha256</code>, despite its known limitations, because we wanted the algorithm to be <a href="https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest">supported in JavaScript</a>, and we weren't sure it was reasonable to expect users attempting to verify file hashes to manually calculate <code>sha512/256</code>.</p>

        <p>Let us know if that sounds correct to you!</p>

        <hr>

        <h2 id="viewing-captured-urls">Viewing Captured URLs</h2>

        <p>The downloadable WACZ files can be played back at <a href="https://replayweb.page">ReplayWeb.page</a> and embedded in your site using using <a href="https://github.com/harvard-lil/wacz-exhibitor">wacz-exhibitor</a>, an <a href="https://lil.law.harvard.edu/blog/2022/09/15/opportunities-and-challenges-of-client-side-playback/">efficient and secure wrapper</a> of ReplayWeb.page's embed system.</p>

        <h3 id="embed-examples">Example</h3>

        <p>The following archive was created using this system: <a href="https://warcembed-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz">https://warcembed-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz</a></p>

        <p>We'll embed a replay of the archive directly in this page:</p>

        <replay-web-page style="display: block; height: 600px; margin-bottom: 1em;"
            source="https://warcembed-demo.s3.amazonaws.com/twitter.com-2020-09-03.wacz"
            url="https://twitter.com/dog_rates/status/1298052245209006086?s=20"
            replaybase="/replay/"
        ></replay-web-page>

        <p>To see more examples of embedded archives, visit the  <a href="https://warcembed-demo.lil.tools/">WACZ-Exhibitor Museum</a></p>

      </div>
    </div>
  </div>
</template>

<script lang="ts">

import TheMainHeader from './TheMainHeader.vue'

import { createNamespacedHelpers } from 'vuex'
const { mapState: mapStateGlobal } = createNamespacedHelpers('globals');
const { mapState: mapStateUsers } = createNamespacedHelpers('user');


export default {
  components: {
     TheMainHeader
  },
  computed: {
    ...mapStateGlobal([
        'rwp_base_url',
    ]),
    ...mapStateUsers([
        'auth_token',
    ]),
    base_url: () => window.location.origin,
    auth_token_key() {
      return this.auth_token?.key || 'your-api-key'
    }
  },
  mounted() {
    const replay = document.createElement('script')
    replay.setAttribute('src', this.rwp_base_url + '/ui.js')
    document.head.appendChild(replay)
  }
}
// script async src="https://platform.twitter.com/widgets.js" charset="utf-8"
</script>

<style lang="scss">
@import "../styles/styles";
@import "../styles/_pages/docs";


</style>
