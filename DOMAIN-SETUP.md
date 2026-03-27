# damelo.sh Domain Setup

Connect the `damelo.sh` domain (GoDaddy) to AWS services via CloudFront + Route 53.

## Architecture

```
damelo.sh  →  CloudFront  →  S3 (damelo-mcp bucket)
                              ↑ serves HTML report pages

App Runner (damelo_bot)  →  MCP endpoint (stays on *.awsapprunner.com or mcp.damelo.sh)
```

- Old S3 links (`damelo-mcp.s3.amazonaws.com/reports/...`) continue working — nothing moves.
- New sessions get `damelo.sh/reports/...` URLs once `damelo_db` returns the new domain in `report_url`.

## Prerequisites

- `damelo.sh` domain on GoDaddy
- AWS account `727646507402` (us-east-1)
- Route 53 hosted zone for `damelo.sh` already created

Route 53 nameservers:
```
ns-336.awsdns-42.com
ns-1181.awsdns-19.org
ns-1876.awsdns-42.co.uk
ns-912.awsdns-50.net
```

## Step 1: Request ACM Certificate

Region **must** be us-east-1 (required for CloudFront).

1. AWS Console → **Certificate Manager** → **Request certificate**
2. Select **Request a public certificate** → Next
3. Domain names:
   - `damelo.sh`
   - `*.damelo.sh` (click "Add another name")
4. Validation method: **DNS validation**
5. Click **Request**
6. ACM shows CNAME records for validation → click **Create records in Route 53** (auto-adds them)
7. Wait for status to change to **Issued** (5–30 min)

## Step 2: Create CloudFront Distribution

1. **CloudFront** → **Create distribution**
2. Origin domain: `damelo-mcp.s3.amazonaws.com`
3. Origin access: **Origin Access Control (OAC)** → create new, type S3
4. Viewer protocol policy: **Redirect HTTP to HTTPS**
5. Alternate domain name (CNAME): `damelo.sh`
6. Custom SSL certificate: select the ACM cert from Step 1
7. Default root object: `index.html` (optional)
8. Click **Create distribution**

CloudFront will show a banner with an S3 bucket policy — **copy and apply it** to the `damelo-mcp` bucket under Permissions → Bucket Policy.

**Important:** Do NOT enable "Block all public access" on the S3 bucket if you want old direct S3 links to keep working.

## Step 3: CloudFront Function for Clean URLs

Strips `.html` from URLs so `damelo.sh/reports/user/abc123` serves the file `reports/user/abc123.html`.

1. **CloudFront** → **Functions** → **Create function**
2. Name: `damelo-clean-urls`
3. Paste this code:

```javascript
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // If URI has no file extension and doesn't end with /, append .html
    if (uri !== '/' && !uri.includes('.') && !uri.endsWith('/')) {
        request.uri = uri + '.html';
    }

    return request;
}
```

4. Click **Save changes** → **Publish**
5. Go to your CloudFront distribution → **Behaviors** → edit the default behavior
6. Under **Function associations** → Viewer request → select `damelo-clean-urls`
7. Save

## Step 4: Route 53 DNS Record

1. **Route 53** → Hosted zones → `damelo.sh`
2. **Create record**:
   - Record name: *(leave empty for apex)*
   - Type: **A**
   - Alias: **Yes**
   - Route traffic to: **Alias to CloudFront distribution**
   - Select your distribution
3. Click **Create records**

## Step 5: Update GoDaddy Nameservers

1. **GoDaddy** → My Products → `damelo.sh` → DNS → Manage
2. Scroll to **Nameservers** → **Change**
3. Select **I'll use my own nameservers**
4. Enter the 4 Route 53 NS records:
   ```
   ns-336.awsdns-42.com
   ns-1181.awsdns-19.org
   ns-1876.awsdns-42.co.uk
   ns-912.awsdns-50.net
   ```
5. Save

Propagation: usually 1–6 hours, can take up to 48h.

## Step 6: Update damelo_db

Change `damelo_db` to return `https://damelo.sh/reports/...` instead of `https://damelo-mcp.s3.amazonaws.com/reports/...` in the `report_url` field.

Also upload files to S3 without the `.html` extension (CloudFront Function handles it), OR keep `.html` in S3 and let the function append it.

## OG Metadata (Link Previews)

For rich link previews (Discord, Slack, Twitter), the HTML reports need Open Graph meta tags in `<head>`:

```html
<meta property="og:title" content="Session Title Here">
<meta property="og:description" content="Session description here">
<meta property="og:image" content="https://damelo.sh/banner.png">
<meta property="og:url" content="https://damelo.sh/reports/user/session-id">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
```

This requires:
1. A static OG banner image uploaded to S3 (`damelo-mcp/og-banner.png`)
2. The session-exporter agent template updated to include OG tags
3. Or inject OG tags server-side in `damelo_db` before uploading to S3
