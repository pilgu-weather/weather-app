        window.onload = () => {

            const params =
                new URLSearchParams(
                    window.location.search
                );

            if (!params.has("lat")) {

                navigator.geolocation.getCurrentPosition(

                    (pos) => {

                        const lat =
                            pos.coords.latitude;

                        const lon =
                            pos.coords.longitude;

                        const selectedDate =
                            params.get("date")
                            || pageContext.selected_date;

                        window.location.href =
                            `/?lat=${lat}&lon=${lon}&date=${selectedDate}`;
                    },

                    () => {

                        console.log("Location denied");
                    }
                );
            }
        };

    

    const carousel =
        document.querySelector(".carousel");

    const dots =
        document.querySelectorAll(".dot");

    if (carousel) {

        carousel.addEventListener("scroll", () => {

            const cardWidth =
                carousel.querySelector(".style-card")
                .offsetWidth + 22;

            const index =
                Math.round(
                    carousel.scrollLeft / cardWidth
                );

            dots.forEach((dot) => {
                dot.classList.remove("active");
            });

            if (dots[index]) {
                dots[index].classList.add("active");
            }

        });

    }

    const shareCard =
        document.getElementById("shareCard");

    const shareCardImage =
        document.getElementById("shareCardImage");

    const shareCardTitle =
        document.getElementById("shareCardTitle");

    const shareCardDesc =
        document.getElementById("shareCardDesc");

    const copyToast =
        document.getElementById("copyToast");

    const calendarButton =
        document.getElementById("calendarButton");

    const calendarPopover =
        document.getElementById("calendarPopover");

    const outfitMenuButtons =
        document.querySelectorAll(".outfit-menu-button");

    const styleImages =
        document.querySelectorAll(".style-image");

    const imageViewer =
        document.getElementById("imageViewer");

    const imageViewerImage =
        document.getElementById("imageViewerImage");

    const imageViewerClose =
        document.getElementById("imageViewerClose");

    const recommendationFeedback =
        document.getElementById("recommendationFeedback");

    const feedbackGood =
        document.getElementById("feedbackGood");

    const feedbackBad =
        document.getElementById("feedbackBad");

    const feedbackReasons =
        document.getElementById("feedbackReasons");

    const feedbackClose =
        document.getElementById("feedbackClose");

    const feedbackOtherReason =
        document.getElementById("feedbackOtherReason");

    const feedbackReasonDetail =
        document.getElementById("feedbackReasonDetail");

    const feedbackSubmit =
        document.getElementById("feedbackSubmit");

    const feedbackThanks =
        document.getElementById("feedbackThanks");

    const reportDialog =
        document.getElementById("reportDialog");

    const reportConfirm =
        document.getElementById("reportConfirm");

    const reportCancel =
        document.getElementById("reportCancel");

    const pageContext = window.WEATHER_FIT_CONTEXT || {};

    const closeCalendar = () => {

        if (!calendarButton || !calendarPopover) {

            return;
        }

        calendarPopover.classList.remove("open");
        calendarButton.setAttribute("aria-expanded", "false");
    };

    if (calendarButton && calendarPopover) {

        calendarButton.addEventListener("click", (event) => {

            event.stopPropagation();

            const isOpen =
                calendarPopover.classList.toggle("open");

            calendarButton.setAttribute(
                "aria-expanded",
                isOpen ? "true" : "false"
            );
        });

        calendarPopover.addEventListener("click", (event) => {

            event.stopPropagation();
        });

        document.addEventListener("click", closeCalendar);

        document.addEventListener("keydown", (event) => {

            if (event.key === "Escape") {

                closeCalendar();
            }
        });
    }

    let pendingReportCard =
        null;

    const closeOutfitMenus = () => {

        document
            .querySelectorAll(".outfit-menu.open")
            .forEach((menu) => {
                menu.classList.remove("open");
            });
    };

    const downloadShareImage = (blob) => {

        const url =
            URL.createObjectURL(blob);

        const link =
            document.createElement("a");

        link.href = url;
        link.download = "weather-fit.png";
        link.click();

        URL.revokeObjectURL(url);
    };

    const getOutfitImageExtension = (imageUrl) => {

        const cleanUrl =
            (imageUrl || "").split("?")[0];

        const match =
            cleanUrl.match(/\.(jpe?g|png|webp)$/i);

        if (!match) {

            return ".jpg";
        }

        return `.${match[1].toLowerCase()}`;
    };

    const getOutfitDownloadName = (styleCard) => {

        const cards =
            Array.from(
                document.querySelectorAll(".style-card")
            );

        const index =
            cards.indexOf(styleCard) + 1;

        const paddedIndex =
            String(Math.max(index, 1)).padStart(3, "0");

        return (
            `weatherfit-outfit-${paddedIndex}`
            + getOutfitImageExtension(
                styleCard
                    ? styleCard.dataset.shareImg
                    : ""
            )
        );
    };

    const getOutfitCardId = (styleCard) => {

        const cards =
            Array.from(
                document.querySelectorAll(".style-card")
            );

        const index =
            cards.indexOf(styleCard) + 1;

        const paddedIndex =
            String(Math.max(index, 1)).padStart(3, "0");

        return `outfit-${paddedIndex}`;
    };

    const triggerImageDownload = (url, filename) => {

        const link =
            document.createElement("a");

        link.href = url;
        link.download = filename;
        link.target = "_blank";

        document.body.appendChild(link);
        link.click();
        link.remove();
    };

    let copyToastTimer;

    const showCopyToast = (message = "링크가 복사되었습니다") => {

        if (!copyToast) {

            return;
        }

        copyToast.textContent =
            message;

        copyToast.classList.add("show");

        clearTimeout(copyToastTimer);

        copyToastTimer =
            setTimeout(() => {

                copyToast.classList.remove("show");

            }, 1800);
    };

    const copyCurrentPageLink = async () => {

        try {

            await navigator.clipboard.writeText(
                window.location.href
            );

        } catch {

            const input =
                document.createElement("textarea");

            input.value =
                window.location.href;

            input.setAttribute("readonly", "");

            input.style.position = "fixed";
            input.style.left = "-9999px";

            document.body.appendChild(input);
            input.select();
            document.execCommand("copy");
            input.remove();
        }

        showCopyToast();
    };

    const openImageViewer = (imageUrl) => {

        if (!imageViewer || !imageViewerImage || !imageUrl) {

            return;
        }

        closeOutfitMenus();

        imageViewerImage.src =
            imageUrl;

        imageViewer.classList.add("open");
        imageViewer.setAttribute("aria-hidden", "false");
    };

    const closeImageViewer = () => {

        if (!imageViewer || !imageViewerImage) {

            return;
        }

        imageViewer.classList.remove("open");
        imageViewer.setAttribute("aria-hidden", "true");
        imageViewerImage.src = "";
    };

    let feedbackCompleted =
        false;

    const postJson = async (url, payload) => {

        const response =
            await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

        if (!response.ok) {

            throw new Error("Request failed");
        }

        return response.json();
    };

    const getCurrentStyleCard = () => {

        const cards =
            Array.from(
                document.querySelectorAll(".style-card")
            );

        if (!cards.length) {

            return null;
        }

        if (!carousel) {

            return cards[0];
        }

        const cardWidth =
            cards[0].offsetWidth + 22;

        const index =
            Math.round(
                carousel.scrollLeft / cardWidth
            );

        return cards[index] || cards[0];
    };

    const saveRecommendationFeedback = async (
        result,
        reasons = [],
        reasonDetail = ""
    ) => {

        const styleCard =
            getCurrentStyleCard();

        await postJson(
            "/feedback",
            {
                ...pageContext,
                outfit_title: styleCard
                    ? styleCard.dataset.shareTitle
                    : "",
                outfit_desc: styleCard
                    ? styleCard.dataset.shareDesc
                    : "",
                rating: result,
                reason: reasons.join(", "),
                reason_detail: reasonDetail,
                page_url: window.location.href
            }
        );
    };

    const completeRecommendationFeedback = (message) => {

        if (!recommendationFeedback || feedbackCompleted) {

            return;
        }

        feedbackCompleted =
            true;

        if (feedbackThanks && message) {

            feedbackThanks.innerHTML =
                message;
        }

        recommendationFeedback.classList.add("thanking");

        setTimeout(() => {

            recommendationFeedback.style.display =
                "none";

        }, 2000);
    };

    const getSelectedFeedbackReasons = () => {

        if (!feedbackReasons) {

            return [];
        }

        return Array.from(
            feedbackReasons.querySelectorAll("input:checked")
        ).map((input) => input.value);
    };

    const updateFeedbackDetailVisibility = () => {

        if (!feedbackOtherReason || !feedbackReasonDetail) {

            return;
        }

        if (feedbackOtherReason.checked) {

            feedbackReasonDetail.classList.add("open");

            return;
        }

        feedbackReasonDetail.classList.remove("open");
        feedbackReasonDetail.value = "";
    };

    const closeFeedbackReasons = () => {

        if (!feedbackReasons) {

            return;
        }

        feedbackReasons.classList.remove("open");

        feedbackReasons
            .querySelectorAll("input:checked")
            .forEach((input) => {
                input.checked = false;
            });

        updateFeedbackDetailVisibility();
    };

    const getOutfitMimeType = (filename) => {

        const lowerName =
            filename.toLowerCase();

        if (lowerName.endsWith(".png")) {

            return "image/png";
        }

        if (lowerName.endsWith(".webp")) {

            return "image/webp";
        }

        return "image/jpeg";
    };

    const loadImageForCanvas = (src) => {

        return new Promise((resolve, reject) => {

            const image =
                new Image();

            image.onload = () => {

                resolve(image);
            };

            image.onerror = reject;
            image.src = src;

        });
    };

    const addWatermarkToImage = async (blob, filename) => {

        const imageUrl =
            URL.createObjectURL(blob);

        try {

            const image =
                await loadImageForCanvas(imageUrl);

            const canvas =
                document.createElement("canvas");

            canvas.width =
                image.naturalWidth || image.width;

            canvas.height =
                image.naturalHeight || image.height;

            const context =
                canvas.getContext("2d");

            context.drawImage(
                image,
                0,
                0,
                canvas.width,
                canvas.height
            );

            const fontSize =
                Math.max(
                    24,
                    Math.min(28, canvas.width * 0.056)
                );

            const padding =
                Math.max(14, canvas.width * 0.035);

            context.save();
            context.globalAlpha = 0.65;
            context.fillStyle = "#ffffff";
            context.font =
                `700 ${fontSize}px -apple-system, BlinkMacSystemFont, sans-serif`;
            context.textAlign = "right";
            context.textBaseline = "bottom";
            context.fillText(
                "Weather Fit",
                canvas.width - padding,
                canvas.height - padding
            );
            context.restore();

            return await new Promise((resolve, reject) => {

                canvas.toBlob(
                    (watermarkedBlob) => {

                        if (!watermarkedBlob) {

                            reject(
                                new Error("Watermark failed")
                            );

                            return;
                        }

                        resolve(watermarkedBlob);
                    },
                    getOutfitMimeType(filename),
                    0.92
                );

            });

        } finally {

            URL.revokeObjectURL(imageUrl);
        }
    };

    const downloadOutfitImage = async (styleCard) => {

        const imageUrl =
            styleCard
                ? styleCard.dataset.shareImg
                : "";

        if (!imageUrl) {

            return;
        }

        const filename =
            getOutfitDownloadName(styleCard);

        try {

            const response =
                await fetch(imageUrl);

            if (!response.ok) {

                throw new Error("Image download failed");
            }

            const blob =
                await response.blob();

            const watermarkedBlob =
                await addWatermarkToImage(blob, filename);

            const blobUrl =
                URL.createObjectURL(watermarkedBlob);

            triggerImageDownload(blobUrl, filename);

            setTimeout(() => {

                URL.revokeObjectURL(blobUrl);

            }, 1000);

        } catch {

            triggerImageDownload(imageUrl, filename);
        }
    };

    const openReportDialog = (styleCard) => {

        pendingReportCard =
            styleCard;

        if (reportDialog) {

            reportDialog.classList.add("open");
            reportDialog.setAttribute("aria-hidden", "false");

            const dialog =
                reportDialog.querySelector(".report-dialog");

            if (dialog) {

                dialog.classList.remove("completed");
            }
        }
    };

    const closeReportDialog = () => {

        pendingReportCard =
            null;

        if (reportDialog) {

            reportDialog.classList.remove("open");
            reportDialog.setAttribute("aria-hidden", "true");
        }
    };

    const saveOutfitReport = async () => {

        const styleCard =
            pendingReportCard;

        if (!styleCard) {

            return;
        }

        await postJson(
            "/report",
            {
                ...pageContext,
                outfit_id: getOutfitCardId(styleCard),
                outfit_image_url: styleCard.dataset.shareImg || "",
                outfit_title: styleCard.dataset.shareTitle || "",
                outfit_desc: styleCard.dataset.shareDesc || "",
                report_reason: "사용자 신고",
                page_url: window.location.href
            }
        );
    };

    const getOutfitImageCandidates = (styleCard) => {

        if (!styleCard) {

            return [];
        }

        try {

            return JSON.parse(
                styleCard.dataset.outfitImages || "[]"
            );

        } catch {

            return [];
        }
    };

    const hideOutfitCard = (styleCard) => {

        const candidates =
            getOutfitImageCandidates(styleCard);

        const currentImage =
            styleCard
                ? styleCard.dataset.shareImg
                : "";

        const nextCandidates =
            candidates.filter((image) => {

                return image !== currentImage;
            });

        if (!styleCard || !nextCandidates.length) {

            showCopyToast("다른 코디가 없습니다");

            return;
        }

        const nextImage =
            nextCandidates[
                Math.floor(
                    Math.random() * nextCandidates.length
                )
            ];

        const styleImage =
            styleCard.querySelector(".style-image");

        if (styleImage) {

            styleImage.src =
                nextImage;
        }

        styleCard.dataset.shareImg =
            nextImage;
    };

    const waitForShareImages = async () => {

        if (!shareCard) {

            return;
        }

        const images =
            Array.from(
                shareCard.querySelectorAll("img")
            );

        await Promise.all(
            images.map((image) => {

                if (image.complete) {

                    return Promise.resolve();
                }

                return new Promise((resolve) => {

                    image.onload = resolve;
                    image.onerror = resolve;

                });

            })
        );
    };

    const prepareShareCard = (styleCard) => {

        if (
            !styleCard
            ||
            !shareCard
            || !shareCardImage
            || !shareCardTitle
            || !shareCardDesc
        ) {

            return false;
        }

        shareCardImage.src =
            styleCard.dataset.shareImg;

        shareCardTitle.textContent =
            styleCard.dataset.shareTitle;

        shareCardDesc.textContent =
            styleCard.dataset.shareDesc;

        return true;
    };

    const shareOutfitCard = async (styleCard) => {

        if (!prepareShareCard(styleCard)) {

            return;
        }

        if (!window.html2canvas) {

            await navigator.clipboard?.writeText(
                window.location.href
            );

            return;
        }

        await waitForShareImages();

        const canvas =
            await html2canvas(shareCard, {
                backgroundColor: null,
                scale: 2,
                useCORS: true
            });

        canvas.toBlob(async (blob) => {

            if (!blob) {

                return;
            }

            const file =
                new File(
                    [blob],
                    "weather-fit.png",
                    { type: "image/png" }
                );

            if (
                navigator.canShare
                && navigator.canShare({ files: [file] })
            ) {

                await navigator.share({
                    files: [file],
                    title: "Weather Fit",
                    text: "오늘의 날씨와 코디를 확인해보세요",
                    url: window.location.href
                });

                return;
            }

            downloadShareImage(blob);

        }, "image/png");
    };

    outfitMenuButtons.forEach((button) => {

        button.addEventListener("click", (event) => {

            event.stopPropagation();

            const menu =
                button.nextElementSibling;

            if (!menu) {

                return;
            }

            const shouldOpen =
                !menu.classList.contains("open");

            closeOutfitMenus();

            if (shouldOpen) {

                menu.classList.add("open");
            }

        });

    });

    styleImages.forEach((image) => {

        let pointerStart = null;

        image.addEventListener("pointerdown", (event) => {

            pointerStart = {
                x: event.clientX,
                y: event.clientY
            };

        });

        image.addEventListener("click", (event) => {

            event.stopPropagation();

            if (pointerStart) {

                const movedX =
                    Math.abs(event.clientX - pointerStart.x);

                const movedY =
                    Math.abs(event.clientY - pointerStart.y);

                if (movedX > 10 || movedY > 10) {

                    return;
                }
            }

            openImageViewer(
                image.currentSrc || image.src
            );

        });

    });

    if (imageViewerClose) {

        imageViewerClose.addEventListener("click", (event) => {

            event.stopPropagation();

            closeImageViewer();

        });
    }

    if (imageViewer) {

        imageViewer.addEventListener("click", (event) => {

            if (event.target === imageViewer) {

                closeImageViewer();
            }

        });
    }

    document
        .querySelectorAll(".outfit-share-action")
        .forEach((button) => {

            button.addEventListener("click", async (event) => {

                event.stopPropagation();

                const styleCard =
                    button.closest(".style-card");

                closeOutfitMenus();

                await shareOutfitCard(styleCard);

            });

        });

    document
        .querySelectorAll(".outfit-copy-action")
        .forEach((button) => {

            button.addEventListener("click", async (event) => {

                event.stopPropagation();

                closeOutfitMenus();

                await copyCurrentPageLink();

            });

        });

    document
        .querySelectorAll(".outfit-download-action")
        .forEach((button) => {

            button.addEventListener("click", async (event) => {

                event.stopPropagation();

                const styleCard =
                    button.closest(".style-card");

                closeOutfitMenus();

                await downloadOutfitImage(styleCard);

            });

        });

    document
        .querySelectorAll(".outfit-report-action")
        .forEach((button) => {

            button.addEventListener("click", (event) => {

                event.stopPropagation();

                const styleCard =
                    button.closest(".style-card");

                closeOutfitMenus();

                openReportDialog(styleCard);

            });

        });

    document
        .querySelectorAll(".outfit-hide-action")
        .forEach((button) => {

            button.addEventListener("click", (event) => {

                event.stopPropagation();

                const styleCard =
                    button.closest(".style-card");

                closeOutfitMenus();

                hideOutfitCard(styleCard);

            });

        });

    if (feedbackGood) {

        feedbackGood.addEventListener("click", async () => {

            try {

                await saveRecommendationFeedback(
                    "딱 맞았어요"
                );

            } catch {

                showCopyToast("저장에 실패했습니다. 잠시 후 다시 시도해주세요.");

                return;
            }

            completeRecommendationFeedback(
                "의견 감사합니다.<br>Weather Fit이 더 똑똑해질게요."
            );

        });
    }

    if (feedbackBad && feedbackReasons) {

        feedbackBad.addEventListener("click", () => {

            feedbackReasons.classList.add("open");

            requestAnimationFrame(() => {

                feedbackReasons.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

            });

        });
    }

    if (feedbackClose) {

        feedbackClose.addEventListener("click", () => {

            closeFeedbackReasons();

        });
    }

    if (feedbackOtherReason) {

        feedbackOtherReason.addEventListener("change", () => {

            updateFeedbackDetailVisibility();

        });
    }

    if (feedbackSubmit) {

        feedbackSubmit.addEventListener("click", async () => {

            const reasons =
                getSelectedFeedbackReasons();

            if (!reasons.length) {

                showCopyToast("사유를 선택해주세요");

                return;
            }

            try {

                await saveRecommendationFeedback(
                    "별로였어요",
                    reasons,
                    feedbackOtherReason && feedbackOtherReason.checked
                        && feedbackReasonDetail
                        ? feedbackReasonDetail.value.trim()
                        : ""
                );

            } catch {

                showCopyToast("저장에 실패했습니다. 잠시 후 다시 시도해주세요.");

                return;
            }

            completeRecommendationFeedback(
                "소중한 의견 감사합니다.<br>더 정확한 추천을 위해 개선하겠습니다."
            );

        });
    }

    if (reportConfirm) {

        reportConfirm.addEventListener("click", async (event) => {

            event.stopPropagation();

            try {

                await saveOutfitReport();

            } catch {

                showCopyToast("저장에 실패했습니다. 잠시 후 다시 시도해주세요.");

                return;
            }

            const dialog =
                reportDialog
                    ? reportDialog.querySelector(".report-dialog")
                    : null;

            if (dialog) {

                dialog.classList.add("completed");
            }

            setTimeout(() => {

                closeReportDialog();

            }, 1000);

        });
    }

    if (reportCancel) {

        reportCancel.addEventListener("click", (event) => {

            event.stopPropagation();

            closeReportDialog();

        });
    }

    if (reportDialog) {

        reportDialog.addEventListener("click", (event) => {

            if (event.target === reportDialog) {

                closeReportDialog();
            }

        });
    }

    document.addEventListener("click", () => {

        closeOutfitMenus();

    });

    (() => {

        const splash =
            document.getElementById("splashScreen");

        if (!splash) {

            return;
        }

        if (sessionStorage.getItem("weatherFitSplashShown")) {

            splash.remove();

            return;
        }

        sessionStorage.setItem(
            "weatherFitSplashShown",
            "true"
        );

        window.addEventListener("load", () => {

            setTimeout(() => {

                splash.classList.add("fade-out");

                setTimeout(() => {

                    splash.remove();

                }, 800);

            }, 2000);

        });
    })();

    if ("serviceWorker" in navigator) {

        window.addEventListener("load", () => {

            navigator.serviceWorker.register(
                "/static/service-worker.js"
            );

        });

    }
