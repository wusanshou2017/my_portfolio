from ultralytics import YOLO
import cv2
import sys
import os
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.pt")

COLORS = {
    "hand": (0, 255, 0),
    "community": (0, 255, 255),
}

WINDOW_COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (255, 128, 0),
    (128, 0, 255),
]


def cluster_cards(card_infos, img_w, img_h):
    if len(card_infos) <= 1:
        return [card_infos]

    positions = np.array([[c["cx"], c["cy"]] for c in card_infos])

    card_h_estimates = [c["bbox"][3] - c["bbox"][1] for c in card_infos]
    card_h = np.median(card_h_estimates) if card_h_estimates else 50

    eps = card_h * 4

    labels = [-1] * len(positions)
    current_label = 0

    for i in range(len(positions)):
        if labels[i] != -1:
            continue
        labels[i] = current_label
        stack = [i]
        while stack:
            idx = stack.pop()
            for j in range(len(positions)):
                if labels[j] != -1:
                    continue
                dist = np.sqrt((positions[idx][0] - positions[j][0]) ** 2 +
                               (positions[idx][1] - positions[j][1]) ** 2)
                if dist < eps:
                    labels[j] = current_label
                    stack.append(j)
        current_label += 1

    groups = {}
    for idx, label in enumerate(labels):
        groups.setdefault(label, []).append(card_infos[idx])

    sorted_groups = sorted(groups.values(), key=lambda g: (
        np.mean([c["cy"] for c in g]),
        np.mean([c["cx"] for c in g])
    ))

    return sorted_groups


def split_hand_community(cards_in_window):
    if len(cards_in_window) <= 2:
        return cards_in_window, []

    sorted_cards = sorted(cards_in_window, key=lambda c: c["cy"])

    card_h = np.median([c["bbox"][3] - c["bbox"][1] for c in sorted_cards])
    gap_threshold = card_h * 1.5

    groups = []
    current_group = [sorted_cards[0]]
    for i in range(1, len(sorted_cards)):
        if sorted_cards[i]["cy"] - current_group[-1]["cy"] < gap_threshold:
            current_group.append(sorted_cards[i])
        else:
            groups.append(current_group)
            current_group = [sorted_cards[i]]
    groups.append(current_group)

    group_avg_y = [(g, np.mean([c["cy"] for c in g])) for g in groups]
    group_avg_y.sort(key=lambda x: x[1], reverse=True)

    hand_group = group_avg_y[0][0]
    community_group = [c for g, _ in group_avg_y[1:] for c in g]

    hand_group.sort(key=lambda c: c["cx"])
    community_group.sort(key=lambda c: c["cx"])

    return hand_group, community_group


def analyze_cards(boxes, img_w, img_h, names):
    card_infos = []
    for box in boxes:
        cls_id = int(box.cls[0])
        cls_name = names[cls_id]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        card_infos.append({
            "cls_name": cls_name,
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2],
            "cx": (x1 + x2) / 2,
            "cy": (y1 + y2) / 2,
        })

    if not card_infos:
        return []

    windows = cluster_cards(card_infos, img_w, img_h)

    results = []
    for win_idx, win_cards in enumerate(windows):
        hand_cards, community_cards = split_hand_community(win_cards)
        results.append({
            "window_id": win_idx,
            "cards": win_cards,
            "hand": hand_cards,
            "community": community_cards,
        })

    return results


def infer(model, image_path, conf=0.25, save=True):
    results = model(image_path, conf=conf)
    img = cv2.imread(image_path)
    if img is None:
        print(f"无法读取图片: {image_path}")
        return results

    img_h, img_w = img.shape[:2]

    for result in results:
        boxes = result.boxes
        print(f"检测到 {len(boxes)} 张牌")

        window_results = analyze_cards(boxes, img_w, img_h, result.names)

        print(f"识别到 {len(window_results)} 个游戏窗口\n")

        for win in window_results:
            win_id = win["window_id"]
            color = WINDOW_COLORS[win_id % len(WINDOW_COLORS)]
            print(f"  --- 窗口 {win_id + 1} ---")

            if win["hand"]:
                hand_str = ", ".join([f"{c['cls_name']}({c['confidence']:.2f})" for c in win["hand"]])
                print(f"  【手牌】({len(win['hand'])} 张): {hand_str}")
            else:
                print(f"  【手牌】: 无")

            if win["community"]:
                comm_str = ", ".join([f"{c['cls_name']}({c['confidence']:.2f})" for c in win["community"]])
                print(f"  【公共牌】({len(win['community'])} 张): {comm_str}")
            else:
                print(f"  【公共牌】: 无")
            print()

            if save:
                all_cards = [("H", c, COLORS["hand"]) for c in win["hand"]] + \
                            [("C", c, COLORS["community"]) for c in win["community"]]
                for prefix, card, draw_color in all_cards:
                    x1, y1, x2, y2 = [int(v) for v in card["bbox"]]
                    cv2.rectangle(img, (x1, y1), (x2, y2), draw_color, 3)
                    cv2.putText(img, f"{prefix}:{card['cls_name']}", (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)

                if win["cards"]:
                    min_x = min(c["bbox"][0] for c in win["cards"]) - 10
                    min_y = min(c["bbox"][1] for c in win["cards"]) - 30
                    max_x = max(c["bbox"][2] for c in win["cards"]) + 10
                    max_y = max(c["bbox"][3] for c in win["cards"]) + 10
                    cv2.rectangle(img, (int(min_x), int(min_y)),
                                  (int(max_x), int(max_y)), color, 2)
                    cv2.putText(img, f"Win{win_id + 1}", (int(min_x), int(min_y) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if save:
            cv2.putText(img, "Green=Hand  Yellow=Community", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            save_path = os.path.splitext(image_path)[0] + "_result.jpg"
            cv2.imwrite(save_path, img)
            print(f"  结果已保存到: {save_path}")

    return results


if __name__ == "__main__":
    model = YOLO(MODEL_PATH)
    conf_thresh = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for i in range(1, 13):
        img_path = os.path.join(base_dir, f"{i}.png")
        if not os.path.exists(img_path):
            print(f"图片不存在: {img_path}")
            continue
        print(f"\n{'=' * 60}")
        print(f"推理图片: {i}.png")
        print(f"{'=' * 60}")
        infer(model, img_path, conf=conf_thresh)
