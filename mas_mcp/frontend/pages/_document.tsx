import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta charSet="utf-8" />
        <meta name="description" content="MAS-MCP Genesis Dashboard - Archaeological Salvage Operations" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <body className="bg-mas-bg text-white antialiased">
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
