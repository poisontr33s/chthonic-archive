import type { NextPageContext } from 'next';

interface ErrorProps {
  statusCode?: number;
}

function Error({ statusCode }: ErrorProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-mas-bg">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-mas-error mb-4">
          {statusCode || 'Error'}
        </h1>
        <p className="text-gray-400 text-xl mb-8">
          {statusCode === 404
            ? 'Page not found'
            : 'An unexpected error occurred'}
        </p>
        <a
          href="/"
          className="text-mas-highlight hover:underline text-lg"
        >
          ← Return to Dashboard
        </a>
      </div>
    </div>
  );
}

Error.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
  return { statusCode };
};

export default Error;
