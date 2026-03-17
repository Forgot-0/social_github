export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 text-center text-sm text-gray-500 sm:px-6 lg:px-8">
        &copy; {new Date().getFullYear()} SocialGH. Платформа для поиска команды и проектов.
      </div>
    </footer>
  );
}
