import { Icon } from "../ui/Icon";
import tiraLogo from "../../assets/tira-logo.jpeg";

export function Topbar({ onOpenMobile }: { onOpenMobile: () => void }) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="topbar-menu-btn"
        onClick={onOpenMobile}
        aria-label="Open navigation menu"
      >
        <Icon name="menu" />
      </button>
      <img className="topbar-logo" src={tiraLogo} alt="" aria-hidden="true" />
      <span className="topbar-title">TIRA</span>
    </header>
  );
}
