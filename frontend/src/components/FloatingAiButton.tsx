import { useLocation, useNavigate } from "react-router-dom";
import { HiOutlineChatBubbleLeftRight } from "react-icons/hi2";


type FloatingAiButtonProps = {
  hidden?: boolean;
};

export default function FloatingAiButton({
      hidden = false,
}: FloatingAiButtonProps) {

    const navigate = useNavigate();
    const location = useLocation();

    // hide the button when already on the AI assistant page
    if (hidden || location.pathname === "/ai-assistant") {
        return null;
    }

    return (
        <button
            type="button"
            onClick={() => navigate("/ai-assistant")}
            aria-label="Open AI travel assistant"
            className="
                fixed bottom-6 right-6 z-50
                flex items-center gap-2
                whitespace-nowrap rounded-full
                border border-white/10
                bg-[#1f2735]/95 px-5 py-3
                text-sm font-medium text-slate-100
                shadow-xl shadow-black/30
                backdrop-blur-md
                transition
                hover:bg-[#2a3445]
                hover:text-amber-300
            "
        >
            <HiOutlineChatBubbleLeftRight className="h-5 w-5 shrink-0 text-amber-400" />
            <span>Travel AI</span>
        </button>
    );
}