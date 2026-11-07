import { createRoot } from "react-dom/client";
import { EmotionReview } from "./features/emotion/EmotionReview";
import "./features/emotion/review.css";
createRoot(document.getElementById("root")!).render(<EmotionReview />);
