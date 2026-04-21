export const createReviewToken = () => {
    if (window.crypto?.randomUUID) {
        return window.crypto.randomUUID()
    }

    return `review_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

export const buildReviewLink = ({ token, versionId }) => {
    const url = new URL(window.location.origin + window.location.pathname)
    url.searchParams.set('reviewToken', token)
    url.searchParams.set('versionId', versionId)
    return url.toString()
}

export const getReviewParamsFromUrl = () => {
    const params = new URLSearchParams(window.location.search)

    return {
        reviewToken: params.get('reviewToken'),
        versionId: params.get('versionId'),
    }
}