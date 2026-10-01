import { getRequestConfig } from "next-intl/server";
import messages from "../../messages/ja.json";

export default getRequestConfig(async () => ({
  locale: "ja",
  messages,
}));
