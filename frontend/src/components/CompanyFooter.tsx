import { Facebook, Instagram, Linkedin, MapPin, Globe, Mail, Youtube } from "lucide-react";

// Replace these defaults with the company's confirmed contact details and official social URLs.
const company = {
  name: import.meta.env.VITE_COMPANY_NAME || "EVIG Integration",
  address: import.meta.env.VITE_COMPANY_ADDRESS || "EVIG Integration Private Limited Plot No. 86, Unit 2, KIADB Industrial Area, Malur, Kolar District, Karnataka 563 130, India",
  email: import.meta.env.VITE_COMPANY_EMAIL || "",
  website: import.meta.env.VITE_COMPANY_WEBSITE || "",
  linkedin: import.meta.env.VITE_COMPANY_LINKEDIN || "",
  facebook: import.meta.env.VITE_COMPANY_FACEBOOK || "",
  instagram: import.meta.env.VITE_COMPANY_INSTAGRAM || "",
};

const socials = [
  { label: "LinkedIn", href: "https://www.linkedin.com/company/evig-integration/", Icon: Linkedin },
  { label: "Facebook", href: "https://www.facebook.com/evigintegration", Icon: Facebook },
  { label: "Instagram", href: "https://instagram.com/evigintegration?igshid=MzRlODBiNWFlZA==", Icon: Instagram },
  { label: "YouTube", href: "https://www.youtube.com/@evigintegration/channels", Icon: Youtube },
  { label: "Website", href: "https://evigintegration.com/", Icon: Globe },
].filter((item) => item.href);

export default function CompanyFooter() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-screen-2xl gap-6 md:grid-cols-[1.2fr_1fr_1fr]">
        <div>
          <p className="text-sm font-bold text-slate-900">{company.name}</p>
          <p className="mt-2 max-w-md text-xs leading-5 text-slate-500">Employee Training &amp; Effectiveness Portal</p>
          <p className="mt-3 text-xs text-slate-500">© {new Date().getFullYear()} {company.name}. All rights reserved.</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-700">Address &amp; location</p>
          <p className="mt-2 flex items-start gap-2 text-sm leading-6 text-slate-600"><MapPin size={16} className="mt-1 shrink-0"/><span>{company.address}</span></p>
          <p className="mt-1 pl-6 text-sm leading-6 text-slate-600">{company.location}</p>
          {company.email && <a href={`mailto:${company.email}`} className="mt-2 inline-flex items-center gap-2 text-sm text-indigo-700 hover:underline"><Mail size={15}/>{company.email}</a>}
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-700">Connect with us</p>
          {socials.length ? <div className="mt-3 flex flex-wrap gap-3">{socials.map(({label,href,Icon}) => <a key={label} href={href} target="_blank" rel="noreferrer" aria-label={label} title={label} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:border-indigo-300 hover:text-indigo-700"><Icon size={16}/>{label}</a>)}</div> : <p className="mt-2 text-sm leading-6 text-slate-500">Official social media links can be configured by the portal administrator.</p>}
        </div>
      </div>
    </footer>
  );
}
